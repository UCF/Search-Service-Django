# Deploying the Search Service to Azure

*Runbook for standing up the dev environment, October 2026. The same steps build QA with `-qa` names. Production cutover is not covered here — see the last section.*

## What this document is for

The hard part of this deployment is not the container. The image already builds and runs: CI builds it on every pull request, runs it against PostgreSQL, and checks that the API answers. What takes care is everything around it, which is six Azure resources, the settings that tell the app where they are, and moving our data from MySQL into PostgreSQL in the right order.

This document walks through that from an empty resource group to a working dev site. It assumes you're comfortable with Azure, the `az` CLI and Docker, and that you don't know Python or Django. **You never need to edit a Python file to deploy this app.** Every setting comes from an environment variable, and every Django task runs as a command inside the container. The next section explains the handful of Django ideas you'll run into.

A first build should take most of a day, though that's an estimate. Most of it is waiting on the PostgreSQL server and on IT for networking.

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

Dev needs six resources in one resource group:

- **Azure Container Registry** holds the image.
- **A user-assigned managed identity** pulls the image, reads Key Vault, and later purges Front Door. One identity for everything keeps the role assignments in one place.
- **Azure Database for PostgreSQL Flexible Server**, version 17, Burstable tier. It replaces the MySQL database on the VMs.
- **Key Vault** holds the database password, the Django secret key, and the API credentials.
- **App Service** on a Linux Basic plan runs the image and serves web traffic.
- **A Container Apps environment** runs the jobs: `migrate`, and the imports.

Front Door, which replaces Varnish as the cache and enforces campus-only access, comes later. The app works without it.

## Before you start

You need the following in hand before step 1. If any are missing, stop and get them, because each one blocks a later step.

- **Access.** Contributor on the subscription or resource group, plus the right to assign roles (User Access Administrator or Owner on the resource group). Without role assignments, the identity can't pull the image or read secrets.
- **Tools.** The `az` CLI (logged in with `az login`, with `az extension add --name containerapp`), Docker or Podman, and a clone of this repository on the branch being deployed. Until `rc-v4.0.0` merges to `master`, that's `rc-v4.0.0`.
- **Networking from IT.** A virtual network with three subnets: one delegated to `Microsoft.DBforPostgreSQL/flexibleServers` for the database, one delegated to `Microsoft.Web/serverFarms` for App Service, and one delegated to `Microsoft.App/environments` (a /27 or larger) for the jobs. The jobs' subnet must reach the campus services the imports call. That should be the same UCF network the QA and production VMs use today. You also need a way to reach the database from your workstation for step 5, either over VPN or from a jump host in the VNet.
- **Values from the VMs.** The credentials in `settings_local.py` on the matching VM (`eduappdev1` for dev, `eduappqaweb1` for QA): the S3 keys and `S3_ENV`, Slate, Kuali, Academic Analytics, the Amazon Comprehend keys, and the MySQL credentials. The appendix lists which variable each value goes into.
- **A copy of the MySQL database.** See step 5.

## Step 1: Set up your shell

Every command below uses these variables. Save them in a file **outside the repository**, such as `~/search-dev.sh`, fill in each `CHANGE_ME`, and run `source ~/search-dev.sh` in each new terminal. The file holds names, not secrets. Secrets go straight into Key Vault in step 4.

```sh
# --- Names. Registry, Key Vault, PostgreSQL and App Service names must be
# globally unique; adjust if Azure says a name is taken. Use -qa for QA.
RG=rg-search-dev
LOCATION=CHANGE_ME          # the region IT uses for the QA and production VMs
ACR=ucfsearchacr            # lowercase letters and numbers only
IDENTITY=id-search-dev
KV=kv-search-dev
PG=psql-search-dev
PLAN=asp-search-dev
APP=app-search-dev
ACA_ENV=cae-search-dev
TAG=CHANGE_ME               # set in step 2, e.g. 64e87d3
IMAGE=$ACR.azurecr.io/search-service:$TAG

# --- Subnet resource IDs from IT
PG_SUBNET_ID=CHANGE_ME
PG_DNS_ZONE_ID=CHANGE_ME    # private DNS zone for PostgreSQL, if IT provides one
WEB_SUBNET_ID=CHANGE_ME
JOBS_SUBNET_ID=CHANGE_ME

# --- App settings that are not secret, shared by the web app and the jobs
SETTINGS=(
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=searchservice
  DB_USER=search_app
  DB_HOST=$PG.postgres.database.azure.com
  DB_PORT=5432
  ALLOWED_HOSTS=$APP.azurewebsites.net,searchdev.cm.ucf.edu
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

# --- Looked up from Azure once the identity exists (step 2)
IDENTITY_ID=$(az identity show -g $RG -n $IDENTITY --query id -o tsv 2>/dev/null)
IDENTITY_CLIENT_ID=$(az identity show -g $RG -n $IDENTITY --query clientId -o tsv 2>/dev/null)
IDENTITY_PRINCIPAL_ID=$(az identity show -g $RG -n $IDENTITY --query principalId -o tsv 2>/dev/null)

# --- The secrets in the two forms App Service and Container Apps expect
WEB_SECRETS=(); JOB_SECRETS=(); JOB_SECRET_ENV=()
for pair in "${SECRETS[@]}"; do
  var=${pair%%:*}; name=${pair#*:}
  WEB_SECRETS+=("$var=@Microsoft.KeyVault(VaultName=$KV;SecretName=$name)")
  JOB_SECRETS+=("$name=keyvaultref:https://$KV.vault.azure.net/secrets/$name,identityref:$IDENTITY_ID")
  JOB_SECRET_ENV+=("$var=secretref:$name")
done

grep -q CHANGE_ME ~/search-dev.sh && echo "Some CHANGE_ME values are still unset."
```

`S3_ENV` decides which folder of the S3 bucket uploaded images go to. Copy it exactly from the VM's `settings_local.py`. If dev points at production's folder, edits on dev change production's images.

The commands in this document follow current `az` documentation, but nobody has run them in our subscription yet. If one fails on a flag, `az <command> --help` usually shows the current spelling, and the portal can do any step by hand. Once step 1 is in place, everything else is copy and paste.

## Step 2: Resource group, identity, registry and image

```sh
az group create -n $RG -l $LOCATION
az identity create -g $RG -n $IDENTITY
source ~/search-dev.sh      # picks up the identity's IDs

az acr create -g $RG -n $ACR --sku Basic
az role assignment create --assignee-object-id $IDENTITY_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal --role AcrPull \
  --scope $(az acr show -n $ACR --query id -o tsv)
```

Build the image in Azure rather than on your laptop. `az acr build` uploads the repository, builds it in Azure, and pushes it to the registry, so it doesn't matter whether your machine is an Apple Silicon Mac. Run it from the root of the repository, and tag the image with the short commit hash so we always know which code is running:

```sh
cd path/to/Search-Service-Django
git status                  # should be clean, on the branch being deployed
git rev-parse --short HEAD  # put this in TAG in ~/search-dev.sh, then source it again
az acr build -r $ACR -t search-service:$TAG --platform linux/amd64 .
```

The build takes a few minutes and ends with `Run ID: ... was successful`. If it fails, the log names the failing line of the `Dockerfile`. Nothing in this step depends on the database, so a failure here is about the build alone.

## Step 3: PostgreSQL

**Decide the network mode with IT before you create the server.** Private access (VNet integration) can't be switched to public access, or back, after creation. We recommend private access, which these commands use. Public access with firewall rules is simpler for dev, but it doesn't match where production will land.

```sh
read -s PG_ADMIN_PASSWORD   # type a strong password; it isn't echoed
az postgres flexible-server create -g $RG -n $PG -l $LOCATION \
  --version 17 --tier Burstable --sku-name Standard_B1ms \
  --storage-size 32 --storage-auto-grow Enabled --backup-retention 7 \
  --admin-user searchadmin --admin-password "$PG_ADMIN_PASSWORD" \
  --subnet $PG_SUBNET_ID --private-dns-zone $PG_DNS_ZONE_ID
```

The server takes 5 to 15 minutes to create. Keep the admin password. It goes into Key Vault in step 4.

Leave the server parameters at their defaults. Specifically:

- **No extensions are needed.** The app uses only standard PostgreSQL, so there's nothing to add to `azure.extensions`.
- **Leave `require_secure_transport` on.** The app's database driver uses TLS automatically when the server offers it, so no setting is needed on our side. We believe this. It hasn't been tested against Azure yet, and step 9 is where it would show up.
- **Leave the time zone at UTC.** Django stores every time in UTC and converts for display itself.
- **Connections are not a concern on B1ms.** The web app opens about three connections per instance and the jobs a handful each, which fits well within what Burstable allows. Move up a size only if the server's CPU stays high during imports.

The app connects as its own role, `search_app`, not as the admin. It owns its database, so it can create and change tables during migrations, and nothing more. From a machine that can reach the server, using PostgreSQL's own image so you don't need `psql` installed:

```sh
docker run --rm -it -e PGPASSWORD="$PG_ADMIN_PASSWORD" postgres:17 \
  psql "host=$PG.postgres.database.azure.com dbname=postgres user=searchadmin sslmode=require"
```

```sql
CREATE ROLE search_app LOGIN PASSWORD 'choose-a-strong-password';
-- On PostgreSQL 16 and later, the admin has to be a member of a role to
-- create a database owned by it.
GRANT search_app TO searchadmin;
CREATE DATABASE searchservice OWNER search_app ENCODING 'UTF8';
\q
```

Leave the new database empty. Step 5 fills it, and the load expects an empty database. That password is `DB_PASSWORD`, and it goes into Key Vault next.

## Step 4: Key Vault and secrets

```sh
az keyvault create -g $RG -n $KV -l $LOCATION --enable-rbac-authorization true
KV_ID=$(az keyvault show -n $KV --query id -o tsv)

# The app's identity reads secrets; you need to write them.
az role assignment create --assignee-object-id $IDENTITY_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" --scope $KV_ID
az role assignment create --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Key Vault Secrets Officer" --scope $KV_ID
```

Role assignments can take a few minutes to apply. If the next command says you're forbidden, wait and retry.

Generate a new `SECRET_KEY` for this environment rather than copying the VM's:

```sh
az keyvault secret set --vault-name $KV -n secret-key \
  --value "$(openssl rand -base64 48 | tr -d '\n/+=')"
az keyvault secret set --vault-name $KV -n postgres-admin-password --value "$PG_ADMIN_PASSWORD"
az keyvault secret set --vault-name $KV -n db-password --value 'the search_app password'
```

Then set one secret for each remaining line of `SECRETS` in step 1, with values from the VM's `settings_local.py`, in the same way. `sentry-dsn` comes from the project's settings in Sentry. When you're done, every secret name in `SECRETS` should appear in:

```sh
az keyvault secret list --vault-name $KV --query "[].name" -o tsv
```

A name that's in `SECRETS` but not in that list will break step 6 or step 7. Either set the secret or delete its line.

## Step 5: Load the data

The challenge here is not copying rows. It is that the two databases describe the same tables differently, and that production is behind the code we're deploying. Production's MySQL is four migrations behind the image. One of those migrations converts a column to JSON, so the data has to be brought current before it moves.

We tested this procedure on September 25 against a copy of production. Every table arrived with matching row counts, and it took a few minutes of machine time. It runs entirely on your workstation in local containers, and then copies the finished PostgreSQL database into Azure:

1. Restore the MySQL copy into a local MySQL 5.7 container, and run the image's migrations against it to bring it current.
2. Create the schema in a local PostgreSQL 17 container by running the image's migrations there.
3. Copy the data from MySQL to PostgreSQL with pgloader.
4. Check the result.
5. Dump the local PostgreSQL database and restore it into Azure.

Steps 1 to 4 are exactly what we rehearsed. **Step 5, the copy into Azure, has not been tested yet.** If it fails, the database in Azure is still empty and can simply be retried.

Work in a folder outside the repository, such as `~/search-data`.

**Get the MySQL copy.** On a machine that can reach the MySQL server, using the credentials from the VM's `settings_local.py`, dump the database without the audit log. The log is almost all of the database's size, and we're not moving it.

```sh
mysqldump --single-transaction --default-character-set=utf8mb4 \
  --ignore-table=searchservice.auditlog_logentry \
  -h eduappmysql1.cc.ucf.edu -u USER -p searchservice > searchservice-prod.sql
```

Dev normally gets a copy of production. Use the QA server (`eduappqamysql1`) instead if you'd rather not touch production. If the database isn't named `searchservice`, change the name here and in the files below.

**Start local MySQL and PostgreSQL.** The `--platform` flag matters only on Apple Silicon Macs, since MySQL 5.7 has no ARM image. It's harmless elsewhere.

```sh
cd ~/search-data
docker network create pl
docker run -d --name pl-mysql --network pl --platform linux/amd64 \
  -e MYSQL_ROOT_PASSWORD=local -e MYSQL_DATABASE=searchservice mysql:5.7
docker run -d --name pl-pg --network pl \
  -e POSTGRES_PASSWORD=local -e POSTGRES_DB=searchservice postgres:17

# Wait about 30 seconds for MySQL to start, then load the copy (a few minutes).
docker exec -i pl-mysql mysql -uroot -plocal --default-character-set=utf8mb4 \
  searchservice < searchservice-prod.sql
```

**Build the image locally**, from the repository at the same commit as `TAG`. This local copy only runs migrations against the two local databases:

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

**Copy it into Azure.** Dump the local PostgreSQL database, then restore it into the empty Azure database as `search_app`, so the app's role owns every table:

```sh
docker exec pl-pg pg_dump -U postgres -Fc --no-owner --no-acl searchservice > searchservice.dump

read -s DB_PASSWORD         # the search_app password
docker run --rm -e PGPASSWORD="$DB_PASSWORD" -v "$PWD":/work postgres:17 \
  pg_restore --no-owner --no-acl --single-transaction \
  -d "host=$PG.postgres.database.azure.com dbname=searchservice user=search_app sslmode=require" \
  /work/searchservice.dump
```

`--single-transaction` makes the restore all or nothing. It prints nothing when it succeeds, and if it fails, the Azure database is left empty and you can retry. Run the row count loop above against Azure if you want a second check. Step 6 checks the result in a different way.

To start dev with an empty database instead of production data, skip all of this. Step 6's `migrate` job builds the empty schema. You'd still need an admin account, which is easiest to create locally against an empty PostgreSQL and restore the same way.

Delete `~/search-data` when dev is working. It holds a copy of production, including users' email addresses and API keys.

## Step 6: Jobs, starting with migrate

Container Apps Jobs run management commands. Every job uses the same image and settings, and only the command differs, so this shell function creates any of them. Add it to `~/search-dev.sh`:

```sh
# create_job NAME CRON COMMAND... — empty CRON means start it by hand
create_job() {
  local name=$1 cron=$2; shift 2
  local trigger=(--trigger-type Manual)
  [ -n "$cron" ] && trigger=(--trigger-type Schedule --cron-expression "$cron")
  az containerapp job create -g $RG -n "$name" --environment $ACA_ENV \
    "${trigger[@]}" --replica-timeout 7200 --replica-retry-limit 0 \
    --parallelism 1 --replica-completion-count 1 --cpu 1 --memory 2Gi \
    --image $IMAGE --registry-server $ACR.azurecr.io --registry-identity $IDENTITY_ID \
    --mi-user-assigned $IDENTITY_ID \
    --secrets "${JOB_SECRETS[@]}" \
    --env-vars "${SETTINGS[@]}" "${JOB_SECRET_ENV[@]}" AZURE_CLIENT_ID=$IDENTITY_CLIENT_ID \
    --command python --args manage.py "$@"
}
```

Create the environment, then the `migrate` job, and run it:

```sh
source ~/search-dev.sh
az containerapp env create -g $RG -n $ACA_ENV -l $LOCATION \
  --infrastructure-subnet-resource-id $JOBS_SUBNET_ID

create_job job-migrate "" migrate
az containerapp job start -g $RG -n job-migrate
az containerapp job execution list -g $RG -n job-migrate -o table   # repeat until Succeeded
```

The job's output is in the environment's Log Analytics workspace. In the portal, open the job, then **Execution history**, then the execution's logs. After step 5, the output should end with `No migrations to apply.` That is the check that the data we loaded and the image agree. Lines starting `Applying` mean the image is newer than the database, which is fine as long as each line ends in `OK`. An error that mentions connecting to the server means the jobs' subnet can't reach PostgreSQL. Take that to IT.

`--replica-timeout 7200` gives every job two hours. We don't yet know how long our longest import runs in Azure, so that's a deliberate overestimate.

`az` reads anything starting with `--` as one of its own options, so arguments like `--no-purge` can't be passed through `create_job`. Create the job without them and add them in the portal, under the job's **Containers** settings.

With migrations done, the database is ready for the web app.

## Step 7: The web app

```sh
az appservice plan create -g $RG -n $PLAN -l $LOCATION --is-linux --sku B1

az webapp create -g $RG -p $PLAN -n $APP \
  --container-image-name $IMAGE --assign-identity $IDENTITY_ID

# Pull the image with the identity, not a password
az webapp config set -g $RG -n $APP --generic-configurations \
  "{\"acrUseManagedIdentityCreds\": true, \"acrUserManagedIdentityID\": \"$IDENTITY_CLIENT_ID\"}"

# Read Key Vault with the same identity
az rest --method PATCH --uri "$(az webapp show -g $RG -n $APP --query id -o tsv)?api-version=2022-03-01" \
  --body "{\"properties\": {\"keyVaultReferenceIdentity\": \"$IDENTITY_ID\"}}"

# Settings, secrets, and the port gunicorn listens on
az webapp config appsettings set -g $RG -n $APP \
  --settings "${SETTINGS[@]}" "${WEB_SECRETS[@]}" WEBSITES_PORT=8000

# Reach PostgreSQL through the VNet, keep the app warm, and probe /healthz
az webapp vnet-integration add -g $RG -n $APP --vnet ${WEB_SUBNET_ID%/subnets/*} --subnet $WEB_SUBNET_ID
az webapp config set -g $RG -n $APP --always-on true \
  --generic-configurations '{"healthCheckPath": "/healthz"}'
az webapp log config -g $RG -n $APP --docker-container-logging filesystem
az webapp restart -g $RG -n $APP
```

**The `*.azurewebsites.net` address is on the public internet** until Front Door and its campus-only rules exist, and dev now holds a copy of production data and an admin login page. Until Front Door is in place, limit the app to campus addresses. Adding one allow rule denies everything else:

```sh
az webapp config access-restriction add -g $RG -n $APP --rule-name campus \
  --action Allow --ip-address CHANGE_ME --priority 100   # UCF's ranges, from IT; repeat per range
```

In the portal, open the app, then **Settings**, then **Environment variables**. Every Key Vault reference should show a green check. A red one means that secret is missing, or the identity can't read it.

## Step 8: Import jobs

Each import is another job from `create_job`. In dev, create them as manual jobs so we can run each one, time it, and compare its results with the VMs before anything runs on a schedule:

```sh
create_job job-import-programs "" import-programs
create_job job-map-units "" map-units
```

The full list of commands is in the `management/commands/` folders of each app in the repository. Three kinds need different things:

- **Database only:** `process-profiles`, `map-units` and `sanitize-unit-names`. These should work as soon as the job exists.
- **Campus and vendor services:** `import-programs`, `import-tuition`, `import-profiles`, `import-catalog-descriptions`, `import-program-application-deadlines`, `import-slate-guids`, `acad-analytics-import-researchers`, `orcid-meta-import`, `import_location_images`, and the podcast commands. These need the credentials from step 4 and a network path from the jobs' subnet to each service. A connection timeout in their logs is a networking question for IT, not an app bug.
- **Files we supply:** `import-cip`, `import-soc`, `import-projection-data`, `import-program-outcome-data`, `import-career-weights`, `import-units` and `import_locations` each read a spreadsheet or data file. We haven't decided how jobs get those files in Azure, so leave these out for now.

Schedules wait until we have an inventory of what runs today and when, which is an open question in the hosting plan. When they come, they're cron expressions in UTC passed as `create_job`'s second argument.

## Step 9: Check that it works

From a campus address:

```sh
curl -s https://$APP.azurewebsites.net/healthz                         # ok
curl -s "https://$APP.azurewebsites.net/api/v1/programs/?limit=1" | head -c 300
curl -sI https://$APP.azurewebsites.net/static/css/style.min.css | head -1   # 200
```

`/healthz` returns `ok` when the app can query the database, and `503` with `database unavailable` when it can't. Then sign in at `https://$APP.azurewebsites.net/manager/login/` with the superuser from step 5, and open a program in the admin. Finally, run `job-map-units` and check that its execution succeeds. That proves the jobs can write to the database.

When all four checks pass, dev is up. Tell the team the address.

## Deploying a new version

Every later release follows the same three moves. **Migrate first, then the web app, then the jobs.**

```sh
# 1. Build the new commit (set TAG in ~/search-dev.sh, then source it)
az acr build -r $ACR -t search-service:$TAG --platform linux/amd64 .

# 2. Migrate with the new image; stop if it doesn't succeed
az containerapp job update -g $RG -n job-migrate --image $IMAGE
az containerapp job start -g $RG -n job-migrate

# 3. Point the web app at it
az webapp config container set -g $RG -n $APP --container-image-name $IMAGE

# 4. Point each import job at it
az containerapp job update -g $RG -n job-import-programs --image $IMAGE
```

Don't update the jobs while an import is running. Wait for it to finish.

Between steps 2 and 3, the old code runs against the new schema for a minute or two. That's fine, because we write migrations that work with the previous release's code. If a release's notes say a migration can't do that, take the site offline for the release rather than deploying it this way. Dev has no deployment slots, so it always updates in place. The GitHub Actions workflow that will do all of this automatically (task 19 in the upgrade plan) hasn't been built yet.

## When something goes wrong

The web app's logs are at `az webapp log tail -g $RG -n $APP`. The jobs' logs are under each job's execution history in the portal.

- **Every page returns 400 Bad Request.** The hostname isn't in `ALLOWED_HOSTS`. The log shows `DisallowedHost` with the hostname to add. Add it to `ALLOWED_HOSTS` in step 1, then rerun the `appsettings set` command. If the health check is what's failing this way, add the hostname it uses. We haven't yet confirmed what `Host` header App Service's probe sends.
- **The container never starts, and the log says it didn't respond on port 80 or 8000.** `WEBSITES_PORT=8000` is missing.
- **`KeyError: 'SECRET_KEY'`, or another variable name, at startup.** A required setting is missing, or its Key Vault reference didn't resolve. Check the green checks under **Environment variables**.
- **Image pull fails, or shows `unauthorized`.** The identity is missing `AcrPull`, or `acrUseManagedIdentityCreds` wasn't set. Role assignments can take several minutes to apply.
- **`/healthz` returns 503.** The app is running but can't reach PostgreSQL. Check the VNet integration, `DB_HOST`, and the `db-password` secret, in that order.
- **A job stops at exactly two hours.** It hit `--replica-timeout`. Raise it on that job, and note the time it needed. That's data we want.
- **An import ends with "the Front Door purge failed".** The import itself finished. The `FRONT_DOOR_*` settings are set but the purge didn't work. In dev, without Front Door, leave them unset and purging does nothing.

If none of these fit, stop and record the full log output.

## Not in this document

- **Production cutover.** It is blocked. Two open fixes, unordered pagination and case-sensitive `plan_code` filters, would return wrong API results on PostgreSQL, and the `teledata` app has to be removed first. Cutover also needs Front Door, single sign-on on the real hostname, and a maintenance window with imports frozen. It should be run as its own planned event, not as an extension of this one.
- **Front Door and campus-only access.** These come after dev is running. When they exist, set the `FRONT_DOOR_*` variables so imports purge the cache, and give the identity a role that can purge the endpoint, such as CDN Endpoint Contributor.
- **Single sign-on.** It needs `searchdev.cm.ucf.edu` pointed at Azure, because the identity provider only knows our existing hostnames. Then set `USE_SAML=true`, `SAML_CLIENT_SETTINGS` (production's configuration as JSON, held in Key Vault) and `SAML_ASSERTION_URL`.

## Appendix: settings reference

`docker/env-settings.py` reads these. Anything not listed keeps the default in `settings_local.tmpl.py`.

| Variable | Secret | What it is |
| --- | --- | --- |
| `SECRET_KEY` | yes | Required. Random, and different in each environment. |
| `DB_ENGINE` | | Required. Always `django.db.backends.postgresql` in Azure. |
| `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | | `DB_NAME` is required. The database from step 3. |
| `DB_PASSWORD` | yes | The `search_app` password. |
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
| `FRONT_DOOR_SUBSCRIPTION_ID`, `_RESOURCE_GROUP`, `_PROFILE`, `_ENDPOINT`, `_DOMAINS` | | The endpoint imports purge. Unset means no purge. |
| `AZURE_CLIENT_ID` | | The identity's client ID, so the jobs purge as it. `create_job` sets it. |
| `WEBSITES_PORT` | | App Service only. Always `8000`. |
