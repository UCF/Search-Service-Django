# Deploying the Search Service to Azure

*Runbook for standing up the dev environment, November 2026. QA follows the same steps with `STAGE=qa` and shares dev's PostgreSQL server. Production cutover is not covered here — see the last section.*

## What this document is for

The hard part of this deployment is not the container. The image already builds and runs: CI builds it on every pull request, runs it against PostgreSQL, and checks that the API answers. What takes care is everything around it — the Azure resources, the private network they sit on, the settings that tell the app where they are, and moving our data from MySQL into PostgreSQL in the right order.

This document walks through that from the resources UCF IT has already provisioned to a working dev site. It assumes you're comfortable with Azure, the `az` CLI and Docker, and that you don't know Python or Django. **You never need to edit a Python file to deploy this app.** Every setting comes from an environment variable, and every Django task runs as a command inside the container. The next section explains the handful of Django ideas you'll run into.

A first build should take most of a day, though that's an estimate. Most of it is waiting on the PostgreSQL upgrade and on the data load.

## The Django you need to know

- **The app is configured entirely by environment variables.** When the container starts, `docker/env-settings.py` reads them. Three are required (`SECRET_KEY`, `DB_ENGINE`, `DB_NAME`), and the app refuses to start without them. The full list is in the appendix.
- **`manage.py` is how you run anything.** Every task is `python manage.py <command>`, run inside the container. In Azure, these run as Container Apps Jobs: a job starts the image, runs one command, and exits.
- **Migrations are the database schema, kept in the repository.** `python manage.py migrate` compares the database against the code and applies whatever schema changes are missing. It records what it applied in a table called `django_migrations`. It is safe to run any number of times. When the database is current, it prints `No migrations to apply.` **The container does not run migrations when it starts.** We run them on purpose, as a job, before pointing the web app at a new image.
- **Imports are also management commands.** Commands such as `import-programs` and `map-units` pull data from Kuali, Slate and other sources into the database. Some run for 20 to 40 minutes, which is why they run as jobs and not on the web app.
- **`ALLOWED_HOSTS` is a list of hostnames.** Django answers only requests whose `Host` header is on the list. Anything else gets `400 Bad Request`. If the site returns 400 for everything, this is almost always why.
- **`SECRET_KEY` signs login sessions.** It is a long random string, and it should be different in each environment. Changing it logs everyone out and does nothing else.
- **A superuser is an admin account** that can sign in at `/manager/login/` with a password. Until single sign-on is set up in Azure, a superuser is the only way into the admin.
- **The web server inside the container is gunicorn, on port 8000.** The container also serves its own CSS and JavaScript, so nothing else is needed for static files.

## What we're building

The resources live in two resource groups. IT built the shared infrastructure, and we build what's specific to the Search Service.

**Infrastructure, `UCFG-USE2-NET-UBMMOONSHOTINFRA-001-RGP`.** IT provisioned and owns these, and other apps may share them:

- **The container registry**, `ucfguse2ubmmoonshotinfracr01`, Premium tier, which holds the image.
- **The Container Apps environment**, `ucfg-use2-net-ubmmoonshotinfra-cae-001`, on a subnet of IT's virtual network. Our web app and jobs run inside it.
- **A Front Door profile**, `UCFG-USE2-NET-UBMMOONSHOTINFRA-FDP-001`, staged with no endpoints yet.
- **A Log Analytics workspace**, `UCFG-USE2-NET-UBMMOONSHOTINFRA-LAW-001`, where the environment's logs should go.
- **An App Service plan**, which we don't use. It's for other teams' apps.

**App, `UCFG-USE2-NET-UBMSEARCHSERVICE-001-RGP`.** We create and own everything here:

- **PostgreSQL Flexible Server**, `ucfg-use2-net-searchservice-pdb-001`. IT created it as a placeholder, and we upgrade it to version 18 and set it up. Dev and QA each get a database on it.
- **A user-assigned managed identity for each environment**, which pulls the image, reads Key Vault, and later purges Front Door. One identity for everything keeps the role assignments in one place.
- **A Key Vault for each environment**, holding the database password, the Django secret key, and the API credentials.
- **A container app** that serves web traffic, and **Container Apps Jobs** that run `migrate` and the imports. They share one set of settings and secrets, so the configuration is written once.

**Everything here is private — none of it has a public address.** The registry and the database are reached through private endpoints, and the Container Apps environment is internal-only. That has three consequences that run through the rest of this document. Images are built on your laptop and pushed over the VPN, not built in Azure. The web app is reachable only from the VPN and campus network until a Front Door endpoint is put in front of it. And the jobs can reach outside services only through IT's central firewall.

## Before you start

You need the following in hand before step 1. If any are missing, stop and get them, because each one blocks a later step.

- **Access.** Contributor on the app resource group, and in the infrastructure group, the right to deploy into the Container Apps environment and to push to the registry. You also need the right to assign roles, both on the app group and on the registry, because the identity needs `AcrPull` there. **Contributor alone doesn't include role assignments** — that takes User Access Administrator, Role Based Access Control Administrator, or Owner. We haven't confirmed what our RBAC grants cover, so check this first.
- **Tools.** The `az` CLI (logged in with `az login`, with `az extension add --name containerapp`), Docker or Podman, the PostgreSQL client `psql` (`brew install libpq` on a Mac, then add `/opt/homebrew/opt/libpq/bin` to your `PATH`), and a clone of this repository checked out at the release being deployed, `v4.1.0` or later.
- **The VPN, with a route to the private endpoints.** Your laptop needs to reach the registry's and the database's private endpoints on the VPN. Private DNS already resolves those names for VPN clients, but a firewall rule may still be needed for the traffic itself. That's a request to IT. Step 2 and step 3 each begin with a check that tells you whether it's in place.
- **Outbound firewall rules for the environment.** The import jobs call services on the public internet, and the environment's outbound traffic goes through IT's firewall. These hosts must be allowed on HTTPS: `www.ucf.edu`, `jobs.ucf.edu`, `map.ucf.edu`, `pub.orcid.org`, `api.academicanalytics.com`, our Kuali and Slate hosts (the `KUALI_BASE_URL` and `SLATE_*_ENDPOINT` values from the VM), Amazon S3 and Amazon Comprehend in `us-east-1`, Sentry, `management.azure.com` for Front Door purges, and `*.vault.azure.net` so the environment can read Key Vault. IT has a firewall request open for the environment, but it was modeled on other apps, so check that these hosts are on it.
- **Values from the VMs.** The credentials in `settings_local.py` on the matching VM (dev's for dev, QA's for QA): the S3 keys and `S3_ENV`, Slate, Kuali, Academic Analytics, the Amazon Comprehend keys, and the MySQL credentials. The appendix lists which variable each value goes into.
- **A copy of the MySQL database.** See step 5.

## Step 1: Set up your shell

Every command below uses these variables. Save them in a file **outside the repository**, such as `~/search-dev.sh`, fill in each `CHANGE_ME`, and run `source ~/search-dev.sh` in each new terminal. The file holds names, not secrets. Secrets go straight into Key Vault in step 4. For QA, copy the file to `~/search-qa.sh` and change `STAGE` and the values copied from the VM.

```sh
STAGE=dev                   # qa for QA

# --- IT's shared resources
INFRA_RG=UCFG-USE2-NET-UBMMOONSHOTINFRA-001-RGP
ACR=ucfguse2ubmmoonshotinfracr01
ACA_ENV=ucfg-use2-net-ubmmoonshotinfra-cae-001
LOCATION=eastus2

# --- Ours. Key Vault names are global and at most 24 characters.
# Adjust these if IT's naming convention says otherwise.
APP_RG=UCFG-USE2-NET-UBMSEARCHSERVICE-001-RGP
PG=ucfg-use2-net-searchservice-pdb-001
PG_ADMIN=CHANGE_ME           # the server's admin user; ask IT or check the portal
PG_IMAGE=postgres:18        # match the server's version after step 3
IDENTITY=ucfg-use2-net-searchservice-id-$STAGE
KV=ucfg-use2-srchsvc-kv-$STAGE
APP=search-$STAGE           # the web app; jobs are named search-dev-<something>
TAG=CHANGE_ME               # set in step 2, e.g. 64e87d3
IMAGE=$ACR.azurecr.io/search-service:$TAG

# --- Looked up from Azure (the identity exists after step 2)
ACA_ENV_ID=$(az containerapp env show -g $INFRA_RG -n $ACA_ENV --query id -o tsv 2>/dev/null)
ENV_DOMAIN=$(az containerapp env show -g $INFRA_RG -n $ACA_ENV --query properties.defaultDomain -o tsv 2>/dev/null)
APP_HOST=$APP.$ENV_DOMAIN   # the web app's address on the VPN
IDENTITY_ID=$(az identity show -g $APP_RG -n $IDENTITY --query id -o tsv 2>/dev/null)
IDENTITY_CLIENT_ID=$(az identity show -g $APP_RG -n $IDENTITY --query clientId -o tsv 2>/dev/null)
IDENTITY_PRINCIPAL_ID=$(az identity show -g $APP_RG -n $IDENTITY --query principalId -o tsv 2>/dev/null)

# --- App settings that are not secret, shared by the web app and the jobs
SETTINGS=(
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=searchservice_$STAGE
  DB_USER=search_$STAGE
  DB_HOST=$PG.postgres.database.azure.com
  DB_PORT=5432
  ALLOWED_HOSTS=$APP_HOST,search$STAGE.cm.ucf.edu
  USE_S3=true
  S3_ENV=CHANGE_ME
  AWS_STORAGE_BUCKET_NAME=ucf-search-service
  AWS_REGION=us-east-1
  KUALI_BASE_URL=CHANGE_ME
  INSTITUTION_GRID_ID=CHANGE_ME
  SLATE_DEADLINES_ENDPOINT=CHANGE_ME
  SLATE_DEADLINES_USERNAME=CHANGE_ME
  SLATE_GUIDS_ENDPOINT=CHANGE_ME
  SLATE_GUIDS_USERNAME=CHANGE_ME
)

# --- Secrets: ENVIRONMENT_VARIABLE:key-vault-secret-name.
# Remove a line if you have no value for it; a reference to a secret
# that doesn't exist breaks the deployment.
SECRETS=(
  SECRET_KEY:secret-key
  DB_PASSWORD:db-password
  AWS_ACCESS_KEY_ID:s3-access-key-id
  AWS_SECRET_ACCESS_KEY:s3-secret-access-key
  AWS_ACCESS_KEY:comprehend-access-key
  AWS_SECRET_KEY:comprehend-secret-key
  SLATE_DEADLINES_PASSWORD:slate-deadlines-password
  SLATE_GUIDS_PASSWORD:slate-guids-password
  KUALI_API_TOKEN:kuali-api-token
  ACADEMIC_ANALYTICS_API_KEY:academic-analytics-api-key
  SENTRY_DSN:sentry-dsn
)

# --- The secrets as Container Apps expects them: each secret is a
# reference to Key Vault, read with the identity, and each environment
# variable points at one secret.
APP_SECRETS=(); SECRET_ENV=()
for pair in "${SECRETS[@]}"; do
  var=${pair%%:*}; name=${pair#*:}
  APP_SECRETS+=("$name=keyvaultref:https://$KV.vault.azure.net/secrets/$name,identityref:$IDENTITY_ID")
  SECRET_ENV+=("$var=secretref:$name")
done

grep -q CHANGE_ME ~/search-$STAGE.sh && echo "Some CHANGE_ME values are still unset."
```

`S3_ENV` decides which folder of the S3 bucket uploaded images go to. Copy it exactly from the VM's `settings_local.py`. If dev points at production's folder, edits on dev change production's images.

The commands in this document follow current `az` documentation, but nobody has run them in our subscription yet. If one fails on a flag, `az <command> --help` usually shows the current spelling, and the portal can do any step by hand. Once step 1 is in place, everything else is copy and paste.

## Step 2: Identity, registry access and image

Create the identity and give it permission to pull from IT's registry:

```sh
az identity create -g $APP_RG -n $IDENTITY -l $LOCATION
source ~/search-$STAGE.sh   # picks up the identity's IDs

az role assignment create --assignee-object-id $IDENTITY_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal --role AcrPull \
  --scope $(az acr show -n $ACR --query id -o tsv)
```

If the role assignment is refused, you don't have the right to assign roles on the registry. Stop and get it (see "Before you start"), since nothing can pull the image without it.

**Build the image on your laptop and push it over the VPN.** `az acr build` doesn't work here: it builds on Azure's own machines, which can't reach a registry with public access turned off. First check that you can reach the registry. Both names should resolve to private addresses (starting `10.`, `172.16.`–`172.31.` or `192.168.`), and the login should end with `Login Succeeded`:

```sh
dig +short $ACR.azurecr.io
dig +short $ACR.$LOCATION.data.azurecr.io
az acr login -n $ACR
```

A timeout here means the VPN has no route to the registry. That's the firewall request in "Before you start". An `unauthorized` error means your account can't push, which needs `AcrPush` or Contributor on the registry.

Then build from the root of the repository, tagged with the short commit hash so we always know which code is running. The `--platform` flag makes an image Azure can run even on an Apple Silicon Mac. Expect that build to be slower, since it runs under emulation:

```sh
cd path/to/Search-Service-Django
git status                  # should be clean, at the release being deployed
git rev-parse --short HEAD  # put this in TAG in ~/search-dev.sh, then source it again
docker build --platform linux/amd64 -t $IMAGE .
docker push $IMAGE
az acr repository show-tags -n $ACR --repository search-service -o tsv   # lists $TAG
```

If the build fails, the log names the failing line of the `Dockerfile`. Nothing in this step depends on the database, so a failure here is about the build alone.

## Step 3: PostgreSQL

The server already exists, behind a private endpoint that IT wired up. We don't create it or change its network — we upgrade it, take ownership of the admin password, and create the app's database. **Every connection needs the password and TLS**, and only machines on the VPN or on IT's virtual network can reach it at all.

**Check that you can reach it.** The server is empty, so the only thing at risk in this step is time. If you don't have the admin password yet, skip ahead to resetting it and come back.

```sh
az postgres flexible-server show -g $APP_RG -n $PG --query "{version:version, sku:sku.name, state:state}" -o table
psql "host=$PG.postgres.database.azure.com dbname=postgres user=$PG_ADMIN sslmode=require" -c "select version();"
```

A hang followed by a timeout means the VPN has no route to the database's private endpoint, which is the same firewall request as the registry's.

**Reset the admin password**, so we hold it and it goes into our Key Vault in step 4. IT set the current one when they created the server, so tell them before you change it, in case anything of theirs uses it:

```sh
read -s PG_ADMIN_PASSWORD   # type a strong password; it isn't echoed
az postgres flexible-server update -g $APP_RG -n $PG --admin-password "$PG_ADMIN_PASSWORD"
```

**Upgrade to PostgreSQL 18.** IT created the server at 17. The app works on both — we rehearsed the data load on each — but CI and local development now run 18, and a major upgrade is far easier on an empty server than a full one. The upgrade takes the server offline for several minutes:

```sh
az postgres flexible-server upgrade -g $APP_RG -n $PG --version 18
```

We believe Azure offers 18 as an in-place upgrade target for this server, but we haven't confirmed it. If the command refuses version 18, stay on 17 for now and set `PG_IMAGE=postgres:17` in `~/search-dev.sh`, so the data load in step 5 matches. Rebuilding the server at 18 instead would need a new private endpoint, and that's IT's work.

**About the tier.** The server is General Purpose, `Standard_D2ds_v5`, because Burstable can't be provisioned in East US 2 or East US right now. IT has a support case open. By our estimate, General Purpose costs about $130 a month against about $15 for Burstable B1ms. When Burstable becomes available, move down in place — it restarts the server but keeps the data:

```sh
az postgres flexible-server update -g $APP_RG -n $PG --tier Burstable --sku-name Standard_B1ms
```

Leave the server parameters at their defaults. Specifically:

- **No extensions are needed.** The app uses only standard PostgreSQL, so there's nothing to add to `azure.extensions`.
- **Leave `require_secure_transport` on.** It's on now. The app's database driver uses TLS automatically when the server offers it, so no setting is needed on our side.
- **Leave the time zone at UTC.** Django stores every time in UTC and converts for display itself.
- **Connections are not a concern.** The web app opens about three connections per replica and the jobs a handful each. That fits on Burstable, and General Purpose allows more.

**Create the app's role and database.** The app connects as its own role, not as the admin. It owns its database, so it can create and change tables during migrations, and nothing more. Dev and QA share this server, so each gets its own role and database — `search_dev` and `searchservice_dev` here, `search_qa` and `searchservice_qa` for QA:

```sh
psql -v admin="$PG_ADMIN" "host=$PG.postgres.database.azure.com dbname=postgres user=$PG_ADMIN sslmode=require"
```

```sql
CREATE ROLE search_dev LOGIN PASSWORD 'choose-a-strong-password';
-- On PostgreSQL 16 and later, the admin has to be a member of a role to
-- create a database owned by it.
GRANT search_dev TO :"admin";
CREATE DATABASE searchservice_dev OWNER search_dev ENCODING 'UTF8';
\q
```

Leave the new database empty. Step 5 fills it, and the load expects an empty database. That password is `DB_PASSWORD`, and it goes into Key Vault next.

## Step 4: Key Vault and secrets

```sh
az keyvault create -g $APP_RG -n $KV -l $LOCATION --enable-rbac-authorization true
KV_ID=$(az keyvault show -n $KV --query id -o tsv)

# The app's identity reads secrets; you need to write them.
az role assignment create --assignee-object-id $IDENTITY_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" --scope $KV_ID
az role assignment create --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Key Vault Secrets Officer" --scope $KV_ID
```

The vault keeps public network access, with every read and write controlled by role. That works with the environment as it stands, as long as `*.vault.azure.net` is on the outbound firewall list. If an Azure Policy refuses to create a vault with public access, the vault needs a private endpoint, and that's a subnet and a DNS record from IT. Role assignments can take a few minutes to apply. If the next command says you're forbidden, wait and retry.

Generate a new `SECRET_KEY` for this environment rather than copying the VM's:

```sh
az keyvault secret set --vault-name $KV -n secret-key \
  --value "$(openssl rand -base64 48 | tr -d '\n/+=')"
az keyvault secret set --vault-name $KV -n postgres-admin-password --value "$PG_ADMIN_PASSWORD"
az keyvault secret set --vault-name $KV -n db-password --value 'the search_dev password'
```

The admin password belongs to the server, not to an environment, so keep it in dev's vault only. QA's vault doesn't need it. Then set one secret for each remaining line of `SECRETS` in step 1, with values from the VM's `settings_local.py`, in the same way. `sentry-dsn` comes from the project's settings in Sentry. When you're done, every secret name in `SECRETS` should appear in:

```sh
az keyvault secret list --vault-name $KV --query "[].name" -o tsv
```

A name that's in `SECRETS` but not in that list will break step 6 or step 7. Either set the secret or delete its line.

## Step 5: Load the data

The challenge here is not copying rows. It is that the two databases describe the same tables differently, and that production is behind the code we're deploying. Production's MySQL is four migrations behind the image. One of those migrations converts a column to JSON, so the data has to be brought current before it moves.

We tested this procedure on September 25 against a copy of production on PostgreSQL 17, and again on November 9 on PostgreSQL 18.6. Both times every table arrived with matching row counts, and it took a few minutes of machine time. It runs entirely on your workstation in local containers, and then copies the finished PostgreSQL database into Azure over the VPN:

1. Restore the MySQL copy into a local MySQL 5.7 container, and run the image's migrations against it to bring it current.
2. Create the schema in a local PostgreSQL container, the same version as Azure's, by running the image's migrations there.
3. Copy the data from MySQL to PostgreSQL with pgloader.
4. Check the result.
5. Dump the local PostgreSQL database and restore it into Azure.

All five steps have been rehearsed. Step 5 was tested against a local database set up the way Azure's is, with an admin that isn't a superuser, but not yet against Azure itself. If it fails there, the database in Azure is still empty and can simply be retried.

Work in a folder outside the repository, such as `~/search-data`.

**Get the MySQL copy.** On a machine that can reach the MySQL server, using the credentials from the VM's `settings_local.py`, dump the database without the audit log. `MYSQL_HOST` and `USER` are the `DATABASES` host and user in that file. The log is almost all of the database's size, and we're not moving it.

```sh
mysqldump --single-transaction --default-character-set=utf8mb4 \
  --ignore-table=searchservice.auditlog_logentry \
  -h MYSQL_HOST -u USER -p searchservice > searchservice-prod.sql
```

Dev normally gets a copy of production. Use the QA MySQL server, from QA's `settings_local.py`, instead if you'd rather not touch production. If the database isn't named `searchservice`, change the name here and in the files below.

**Start local MySQL and PostgreSQL.** The `--platform` flag matters only on Apple Silicon Macs, since MySQL 5.7 has no ARM image. It's harmless elsewhere.

```sh
cd ~/search-data
docker network create pl
docker run -d --name pl-mysql --network pl --platform linux/amd64 \
  -e MYSQL_ROOT_PASSWORD=local -e MYSQL_DATABASE=searchservice mysql:5.7
docker run -d --name pl-pg --network pl \
  -e POSTGRES_PASSWORD=local -e POSTGRES_DB=searchservice $PG_IMAGE

# Wait about 30 seconds for MySQL to start, then load the copy (a few minutes).
docker exec -i pl-mysql mysql -uroot -plocal --default-character-set=utf8mb4 \
  searchservice < searchservice-prod.sql
```

**Build the image locally for your own machine**, from the repository at the same commit as `TAG`. This copy only runs migrations against the two local databases, so it doesn't need the `--platform` flag from step 2:

```sh
docker build -t search-service:load path/to/Search-Service-Django
```

Create two settings files in `~/search-data`. They point the image at each local database.

`mysql.env`:

```
SECRET_KEY=local-load
DB_ENGINE=django.db.backends.mysql
DB_NAME=searchservice
DB_USER=root
DB_PASSWORD=local
DB_HOST=pl-mysql
DB_PORT=3306
```

`pg.env`:

```
SECRET_KEY=local-load
DB_ENGINE=django.db.backends.postgresql
DB_NAME=searchservice
DB_USER=postgres
DB_PASSWORD=local
DB_HOST=pl-pg
DB_PORT=5432
```

**Bring both databases current:**

```sh
docker run --rm --network pl --env-file mysql.env search-service:load python manage.py migrate
docker run --rm --network pl --env-file pg.env search-service:load python manage.py migrate
```

The MySQL run applies a few migrations, four in our rehearsal, and each ends in `OK`. The PostgreSQL run applies every migration from scratch, about a hundred lines of `Applying ... OK`. Any line that doesn't end in `OK` is a stop. Send the output to the team.

**Copy the data.** Save this as `load.pgloader`. It loads data only into the tables Django just created, and keeps PostgreSQL's own migration history rather than MySQL's:

```
LOAD DATABASE
  FROM mysql://root:local@pl-mysql/searchservice
  INTO postgresql://postgres:local@pl-pg/searchservice

WITH data only, truncate, disable triggers, reset sequences

EXCLUDING TABLE NAMES MATCHING 'django_migrations'

ALTER SCHEMA 'searchservice' RENAME TO 'public';
```

```sh
docker run --rm --network pl --platform linux/amd64 -v "$PWD":/work \
  dimitri/pgloader:latest pgloader /work/load.pgloader
```

Use the `dimitri/pgloader` image, which is version 3.6.7. Version 3.6.10, the one some package managers install, fails against MySQL 5.7. pgloader ends with a summary table. The `errors` column should be 0 on every row, and the last line should read `Total import time ✓`. Warnings about `auditlog_logentry` column types are expected and harmless.

**Check the result.** Compare row counts table by table:

```sh
for t in $(docker exec pl-pg psql -U postgres -d searchservice -tAc \
    "select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' order by 1"); do
  pg=$(docker exec pl-pg psql -U postgres -d searchservice -tAc "select count(*) from \"$t\"")
  my=$(docker exec pl-mysql mysql -uroot -plocal -N searchservice -e "select count(*) from \`$t\`" 2>/dev/null)
  [ "$pg" = "$my" ] || echo "DIFFERENT: $t mysql=$my postgres=$pg"
done
```

It may print `auditlog_logentry`, which we left out of the dump, and `django_migrations`, which each database writes for itself. Any other table is a stop.

**Create an admin account.** Production's accounts sign in through single sign-on and have no passwords, and SSO won't work in Azure until the dev hostname moves there. Create a superuser now, so it travels with the data. It asks for a username, email and password:

```sh
docker run --rm -it --network pl --env-file pg.env search-service:load python manage.py createsuperuser
```

Don't do this for a production load.

**Copy it into Azure.** Dump the local PostgreSQL database, then restore it into the empty Azure database as the app's role, so that role owns every table. You need to be on the VPN:

```sh
docker exec pl-pg pg_dump -U postgres -Fc --no-owner --no-acl searchservice > searchservice.dump

read -s DB_PASSWORD         # the search_dev password
docker run --rm -e PGPASSWORD="$DB_PASSWORD" -v "$PWD":/work $PG_IMAGE \
  pg_restore --no-owner --no-acl --single-transaction \
  -d "host=$PG.postgres.database.azure.com dbname=searchservice_$STAGE user=search_$STAGE sslmode=require" \
  /work/searchservice.dump
```

`--single-transaction` makes the restore all or nothing. It prints nothing when it succeeds, and if it fails, the Azure database is left empty and you can retry. If it can't connect while `psql` from step 3 can, the container isn't using the VPN's DNS. Replace the hostname with the address `dig +short $PG.postgres.database.azure.com` prints, keeping `sslmode=require`. Run the row count loop above against Azure if you want a second check. Step 6 checks the result in a different way.

To start dev with an empty database instead of production data, skip all of this. Step 6's `migrate` job builds the empty schema, and once the web app is running you can create an admin account in it with `az containerapp exec` (see "One-off commands" below).

Delete `~/search-data` when dev is working. It holds a copy of production, including users' email addresses and API keys.

## Step 6: Jobs, starting with migrate

**First, check that the environment sends logs somewhere.** Job output is the only way to see what a job did, and the environment is IT's, so this is a check rather than a change:

```sh
az containerapp env show -g $INFRA_RG -n $ACA_ENV --query properties.appLogsConfiguration -o json
```

It should name a `log-analytics` destination with a workspace ID. If it's empty, the environment needs pointing at `UCFG-USE2-NET-UBMMOONSHOTINFRA-LAW-001`. That's a change to a shared environment, so agree it with IT before making it.

Container Apps Jobs run management commands. Every job uses the same image and settings, and only the command differs, so this shell function creates any of them. Job names are prefixed with the app name so dev's and QA's don't collide in our resource group, and names can't be longer than 32 characters. Add it to `~/search-dev.sh`:

```sh
# create_job NAME CRON COMMAND... — makes job $APP-NAME; empty CRON means start it by hand
create_job() {
  local name=$APP-$1 cron=$2; shift 2
  local trigger=(--trigger-type Manual)
  [ -n "$cron" ] && trigger=(--trigger-type Schedule --cron-expression "$cron")
  az containerapp job create -g $APP_RG -n "$name" --environment $ACA_ENV_ID \
    "${trigger[@]}" --replica-timeout 7200 --replica-retry-limit 0 \
    --parallelism 1 --replica-completion-count 1 --cpu 1 --memory 2Gi \
    --image $IMAGE --registry-server $ACR.azurecr.io --registry-identity $IDENTITY_ID \
    --mi-user-assigned $IDENTITY_ID \
    --secrets "${APP_SECRETS[@]}" \
    --env-vars "${SETTINGS[@]}" "${SECRET_ENV[@]}" AZURE_CLIENT_ID=$IDENTITY_CLIENT_ID \
    --command python --args manage.py "$@"
}
```

The environment lives in IT's resource group, so `--environment` takes its full resource ID rather than its name. Create the `migrate` job and run it:

```sh
echo $APP_HOST              # should be search-dev.<something>.eastus2.azurecontainerapps.io
create_job migrate "" migrate
az containerapp job start -g $APP_RG -n $APP-migrate
az containerapp job execution list -g $APP_RG -n $APP-migrate -o table   # repeat until Succeeded
```

The job's output is in the Log Analytics workspace. In the portal, open the job, then **Execution history**, then the execution's logs. After step 5, the output should end with `No migrations to apply.` That is the check that the data we loaded and the image agree. Lines starting `Applying` mean the image is newer than the database, which is fine as long as each line ends in `OK`.

Two failures are specific to this network. An error pulling the image means the identity is missing `AcrPull`, or the environment can't reach the registry's private endpoint. An error connecting to the database means the environment's subnet can't reach the database's private endpoint. Your laptop reaching it says nothing about whether the environment can, since they take different routes. Either one needs IT to look at the route between the subnet and the private endpoint.

`--replica-timeout 7200` gives every job two hours. We don't yet know how long our longest import runs in Azure, so that's a deliberate overestimate.

`az` reads anything starting with `--` as one of its own options, so arguments like `--no-purge` can't be passed through `create_job`. Create the job without them and add them in the portal, under the job's **Containers** settings.

With migrations done, the database is ready for the web app.

## Step 7: The web app

The web app is a container app in the same environment, with the same image, settings and secrets as the jobs. The differences are that it keeps running, and that it accepts traffic on gunicorn's port:

```sh
az containerapp create -g $APP_RG -n $APP --environment $ACA_ENV_ID \
  --image $IMAGE --registry-server $ACR.azurecr.io --registry-identity $IDENTITY_ID \
  --user-assigned $IDENTITY_ID \
  --ingress external --target-port 8000 \
  --cpu 0.5 --memory 1Gi --min-replicas 0 --max-replicas 2 \
  --secrets "${APP_SECRETS[@]}" \
  --env-vars "${SETTINGS[@]}" "${SECRET_ENV[@]}"
```

If a Key Vault secret is missing, or the identity can't read it, the command fails or the app never starts, and the error names the secret. Fix it and run the same command again.

**`--ingress external` doesn't mean the internet.** The environment is internal-only, so "external" here means reachable from outside the environment — from IT's virtual network, and from the VPN and campus network through IT's DNS. The app's address is `https://$APP_HOST`. Nobody off the VPN can reach it until a Front Door endpoint sits in front of it (see "Not in this document"). Container Apps provides the HTTPS certificate for that address and redirects plain HTTP to it.

**Dev scales to zero.** With `--min-replicas 0`, nothing runs while nobody is using the site, and we pay almost nothing for it. The cost is that the first request after a quiet stretch waits while a container starts. We haven't measured how long that takes; we expect seconds, not minutes. QA should use `--min-replicas 1` so content editors don't hit that wait, and production should run at least two.

Container Apps checks that the container is alive by connecting to port 8000, which is enough for dev. Our `/healthz` endpoint goes further and checks the database too. Switching the probe to `/healthz` needs a `Host` header that's in `ALLOWED_HOSTS`, since Django rejects any other hostname. That's a change to make before production, in the portal under the app's **Containers**, then **Health probes**.

## Step 8: Import jobs

Each import is another job from `create_job`. In dev, create them as manual jobs so we can run each one, time it, and compare its results with the VMs before anything runs on a schedule:

```sh
create_job import-programs "" import-programs
create_job map-units "" map-units
```

The full list of commands is in the `management/commands/` folders of each app in the repository. Three kinds need different things:

- **Database only:** `process-profiles`, `map-units` and `sanitize-unit-names`. These should work as soon as the job exists, with one known exception. `map-units` can fail on PostgreSQL with `MultipleObjectsReturned`, or give different results from run to run, until the fix for unordered queries (task 15 in the upgrade plan) merges. A failure there is that bug, not a deployment problem.
- **Outside services:** `import-programs`, `import-tuition`, `import-profiles`, `import-catalog-descriptions`, `import-program-application-deadlines`, `import-slate-guids`, `acad-analytics-import-researchers`, `orcid-meta-import`, `import_location_images`, and the podcast commands. These need the credentials from step 4 and an outbound firewall rule for each service they call. A connection timeout in their logs almost always means the host isn't on IT's allow list yet. Note which host it is — the log names it — and add it to the firewall request rather than changing anything in the app.
- **Files we supply:** `import-cip`, `import-soc`, `import-projection-data`, `import-program-outcome-data`, `import-career-weights`, `import-units` and `import_locations` each read a spreadsheet or data file. We haven't decided how jobs get those files in Azure, so leave these out for now.

Schedules wait until we have an inventory of what runs today and when, which is an open question in the hosting plan. When they come, they're cron expressions in UTC passed as `create_job`'s second argument.

## Step 9: Check that it works

From a machine on the VPN:

```sh
curl -s https://$APP_HOST/healthz                         # ok
curl -s "https://$APP_HOST/api/v1/programs/?limit=1" | head -c 300
curl -sI https://$APP_HOST/static/css/style.min.css | head -1   # 200
```

If `curl` can't resolve the address, the VPN isn't serving DNS for the environment's domain. Check with `dig +short $APP_HOST`, which should return the environment's private address, the same one `az containerapp env show -g $INFRA_RG -n $ACA_ENV --query properties.staticIp -o tsv` prints. The first request may take a few seconds while dev scales up from zero. `/healthz` returns `ok` when the app can query the database, and `503` with `database unavailable` when it can't.

Then sign in at `https://$APP_HOST/manager/login/` with the superuser from step 5, and open a program in the admin. Finally, create a `process-profiles` job (`create_job process-profiles "" process-profiles`), run it, and check that its execution succeeds. That proves the jobs can write to the database.

When all four checks pass, dev is up. Tell the team the address, and that it works only on the VPN for now.

## Deploying a new version

Every later release follows the same three moves. **Migrate first, then the web app, then the jobs.**

```sh
# 1. Build and push the new commit (set TAG in ~/search-dev.sh, then source it), on the VPN
az acr login -n $ACR
docker build --platform linux/amd64 -t $IMAGE . && docker push $IMAGE

# 2. Migrate with the new image; stop if it doesn't succeed
az containerapp job update -g $APP_RG -n $APP-migrate --image $IMAGE
az containerapp job start -g $APP_RG -n $APP-migrate

# 3. Point the web app at it
az containerapp update -g $APP_RG -n $APP --image $IMAGE

# 4. Point each import job at it
az containerapp job update -g $APP_RG -n $APP-import-programs --image $IMAGE
```

Don't update the jobs while an import is running. Wait for it to finish.

Updating the web app starts a new revision, which is Container Apps' word for a running version. The old revision keeps serving until the new one is up, then traffic moves over. There are no slots to swap. To roll back, run step 3 with the previous tag. That doesn't undo the migration from step 2, which is why we write migrations that work with the previous release's code. If a release's notes say a migration can't do that, take the site offline for the release rather than deploying it this way.

The GitHub Actions workflow that will do all of this automatically (task 19 in the upgrade plan) hasn't been built yet, and it has a new obstacle: GitHub's runners can't reach a private registry. It will need either a runner inside our network or an ACR dedicated agent pool, and both need a subnet from IT.

To change a setting without a new image, use `az containerapp update -g $APP_RG -n $APP --set-env-vars NAME=value`, and the same with `az containerapp job update` for each job. The settings in `~/search-dev.sh` only apply when something is created, so update the file too.

### One-off commands

For a quick command that isn't worth a job, such as creating an admin account, open a shell in the running web app:

```sh
curl -s https://$APP_HOST/healthz    # wakes dev up if it has scaled to zero
az containerapp exec -g $APP_RG -n $APP --command "python manage.py createsuperuser"
```

Anything that runs longer than a minute or two belongs in a job instead. The web app's containers can be replaced at any time.

## When something goes wrong

The web app's logs are at `az containerapp logs show -g $APP_RG -n $APP --follow`. Add `--type system` to see Azure's side, such as image pulls and containers failing to start. The jobs' logs are under each job's execution history in the portal.

- **Every page returns 400 Bad Request.** The hostname isn't in `ALLOWED_HOSTS`. The log shows `DisallowedHost` with the hostname to add. Add it to `ALLOWED_HOSTS` with `--set-env-vars` (see "Deploying a new version") and in `~/search-dev.sh`. An `APP_HOST` that's just `search-dev.` means `az` wasn't logged in when you sourced `~/search-dev.sh`.
- **The app never becomes ready, and the system log shows the port check failing.** The target port isn't 8000. Fix it with `az containerapp ingress update -g $APP_RG -n $APP --target-port 8000`.
- **`KeyError: 'SECRET_KEY'`, or another variable name, at startup.** A required setting is missing. Compare the app's **Environment variables** in the portal with `SETTINGS` and `SECRETS`.
- **Image pull fails, or shows `unauthorized`.** The identity is missing `AcrPull` on IT's registry, or the app wasn't created with `--registry-identity`. Role assignments can take several minutes to apply. If the role is there, the environment may not be able to reach the registry's private endpoint, which is IT's to check.
- **Secrets fail to load and the error mentions Key Vault.** Either the identity lacks `Key Vault Secrets User`, or the environment can't reach `*.vault.azure.net` through the firewall.
- **`/healthz` returns 503.** The app is running but can't reach PostgreSQL. Check `DB_HOST`, then the `db-password` secret, then whether the environment's subnet can reach the database's private endpoint.
- **`docker push` or `psql` hangs from your laptop.** The VPN has no route to the private endpoint. Check that you're connected, then that the names resolve to private addresses with `dig`. If both are fine, it's the VPN firewall rule.
- **A job stops at exactly two hours.** It hit `--replica-timeout`. Raise it on that job, and note the time it needed. That's data we want.
- **An import ends with "the Front Door purge failed".** The import itself finished. The `FRONT_DOOR_*` settings are set but the purge didn't work. In dev, without a Front Door endpoint, leave them unset and purging does nothing.

If none of these fit, stop and record the full log output.

## Not in this document

- **Production cutover.** It is blocked. Two open fixes, unordered pagination and case-sensitive `plan_code` filters, would return wrong API results on PostgreSQL, and the `teledata` app has to be removed first. Cutover also needs Front Door, single sign-on on the real hostname, and a maintenance window with imports frozen. It should be run as its own planned event, not as an extension of this one.
- **Production's database.** Production should get its own server, not a third database on dev's, and IT recommends General Purpose or above for it. It will need its own private endpoint, which is IT's work.
- **Front Door.** It's what gives the app an address off the VPN. That means an endpoint on IT's profile with the web app as a Private Link origin, which needs the profile to be on the Premium tier. Check that with `az afd profile show -g $INFRA_RG --profile-name UCFG-USE2-NET-UBMMOONSHOTINFRA-FDP-001 --query sku.name`. The Private Link connection then has to be approved on the environment, which is in IT's group. Once the endpoint exists, set the `FRONT_DOOR_*` variables so imports purge the cache, and give the identity a role that can purge the endpoint, such as CDN Endpoint Contributor.
- **Single sign-on.** It needs `searchdev.cm.ucf.edu` pointed at Azure, through Front Door, because the identity provider only knows our existing hostnames. Then set `USE_SAML=true`, `SAML_CLIENT_SETTINGS` (production's configuration as JSON, held in Key Vault) and `SAML_ASSERTION_URL`.

## Appendix: settings reference

`docker/env-settings.py` reads these. Anything not listed keeps the default in `settings_local.tmpl.py`.

| Variable | Secret | What it is |
| --- | --- | --- |
| `SECRET_KEY` | yes | Required. Random, and different in each environment. |
| `DB_ENGINE` | | Required. Always `django.db.backends.postgresql` in Azure. |
| `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | | `DB_NAME` is required. The database and role from step 3, one pair per environment. |
| `DB_PASSWORD` | yes | That role's password. |
| `ALLOWED_HOSTS` | | Comma-separated hostnames the site answers to. |
| `DEBUG` | | Leave unset. `true` shows error details to visitors. |
| `USE_S3`, `S3_ENV`, `AWS_STORAGE_BUCKET_NAME` | | Uploaded images go to S3. `S3_ENV` is the bucket folder, copied from the VM. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | yes | S3 keys. |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION` | keys yes | Amazon Comprehend, used by `import-catalog-descriptions`. These are separate from the S3 keys, despite the similar names. |
| `SLATE_DEADLINES_ENDPOINT`, `_USERNAME`, `_PASSWORD`, and the same for `SLATE_GUIDS_` | passwords yes | Graduate Studies' Slate. |
| `KUALI_BASE_URL`, `KUALI_API_TOKEN` | token yes | The catalog. |
| `ACADEMIC_ANALYTICS_API_KEY`, `INSTITUTION_GRID_ID` | key yes | Research imports. |
| `SENTRY_DSN` | yes | Error reporting. |
| `USE_SAML`, `SAML_CLIENT_SETTINGS`, `SAML_ASSERTION_URL` | settings yes | Single sign-on. Off until the hostname moves. |
| `FRONT_DOOR_SUBSCRIPTION_ID`, `_RESOURCE_GROUP`, `_PROFILE`, `_ENDPOINT`, `_DOMAINS` | | The endpoint imports purge. Unset means no purge. The profile is `UCFG-USE2-NET-UBMMOONSHOTINFRA-FDP-001` in the infrastructure group. |
| `AZURE_CLIENT_ID` | | The identity's client ID, so the jobs purge as it. `create_job` sets it. |
