# Deploying the Search Service to Azure, in the portal

*Runbook for standing up the dev environment through the Azure portal, November 2026. QA follows the same steps with `qa` in place of `dev` and shares dev's PostgreSQL server. The same deployment done with the `az` CLI is in [azure-deployment.md](azure-deployment.md). Production cutover is not covered here — see the last section.*

## What this document is for

The challenge here is not the container. The image already builds and runs: CI builds it on every pull request, runs it against PostgreSQL, and checks that the API answers. What takes care is everything around it — the Azure resources, the private network they sit on, the settings that tell the app where they are, and moving our data from MySQL into PostgreSQL in the right order.

This version does everything the portal can do in the portal. Three things it can't, and those stay in a terminal: building and pushing the image, running a few lines of SQL against the database, and loading the data. **The portal is slower for the app's settings than the CLI.** The web app and every job each need the same eleven secrets and sixteen settings entered by hand, so expect the jobs in steps 6 and 8 to be the longest part of the day. If you find yourself creating more than three or four jobs, the CLI runbook's `create_job` function does each one in a single command.

It assumes you're comfortable with Azure and that you don't know Python or Django. **You never need to edit a Python file to deploy this app.** Portal labels move around from time to time. If a button isn't where this document says, the setting almost always exists under a nearby name.

## The Django you need to know

- **The app is configured entirely by environment variables.** Three are required (`SECRET_KEY`, `DB_ENGINE`, `DB_NAME`), and the app refuses to start without them. The full list is in step 1.
- **`manage.py` is how you run anything.** Every task is `python manage.py <command>`, run inside the container. In Azure, these run as Container Apps Jobs: a job starts the image, runs one command, and exits.
- **Migrations are the database schema.** `python manage.py migrate` applies whatever schema changes the database is missing, and is safe to run any number of times. When the database is current, it prints `No migrations to apply.` **The container does not run migrations when it starts.** We run them on purpose, as a job, before pointing the web app at a new image.
- **Imports are also management commands.** Commands such as `import-programs` pull data from Kuali, Slate and other sources. Some run for 20 to 40 minutes, which is why they run as jobs.
- **`ALLOWED_HOSTS` is a list of hostnames.** Django answers only requests whose `Host` header is on the list, and returns `400 Bad Request` for anything else. If the site returns 400 for everything, this is almost always why.
- **`SECRET_KEY` signs login sessions.** A long random string, different in each environment.
- **A superuser is an admin account** that signs in at `/manager/login/` with a password. Until single sign-on is set up in Azure, it's the only way into the admin.
- **The web server inside the container listens on port 8000**, and serves its own CSS and JavaScript.

## What we're building

The resources live in two resource groups that already exist. We don't create any resource groups.

**Infrastructure, `UCFG-USE2-NET-UBMMOONSHOTINFRA-001-RGP`.** IT provisioned and owns these:

- **The container registry**, `ucfguse2ubmmoonshotinfracr01`, which holds the image.
- **The Container Apps environment**, `ucfg-use2-net-ubmmoonshotinfra-cae-001`, on IT's virtual network. The web app and jobs we create run inside it, though they belong to our resource group.
- **A Front Door profile**, `UCFG-USE2-NET-UBMMOONSHOTINFRA-FDP-001`, with no endpoints yet.
- **A Log Analytics workspace**, `UCFG-USE2-NET-UBMMOONSHOTINFRA-LAW-001`, where the environment's logs should go.

**App, `UCFG-USE2-NET-UBMSEARCHSERVICE-001-RGP`.** We create and own everything here:

- **PostgreSQL Flexible Server**, `ucfg-use2-net-searchservice-pdb-001`, which IT created as a placeholder. We upgrade it and set it up.
- **A managed identity, a Key Vault, a web app and its jobs** for each environment.

**Everything is private — none of it has a public address.** You'll need the VPN for every step that touches the registry or the database, the web app is reachable only from the VPN and campus network until a Front Door endpoint sits in front of it, and the jobs reach outside services only through IT's central firewall.

## Before you start

You need the following before step 1. Each one blocks a later step.

- **Access.** Contributor on the app resource group, plus the right to deploy into the Container Apps environment and to push to the registry in the infrastructure group. You also need to assign roles on the app group and on the registry. **Contributor alone doesn't include role assignments**; that takes User Access Administrator, Role Based Access Control Administrator, or Owner. Check this first: open the registry, then **Access control (IAM)**, then **Add**. If **Add role assignment** is greyed out, you don't have it.
- **Tools for the terminal steps.** Docker or Podman, the `az` CLI (only for `az acr login` in step 2), the PostgreSQL client `psql` (`brew install libpq` on a Mac), and a clone of this repository at the release being deployed, `v4.1.0` or later.
- **The VPN, with a route to the private endpoints.** Your laptop has to reach the registry and the database on the VPN. Steps 2 and 3 each begin with a check. If either times out, it's a firewall request to IT.
- **Outbound firewall rules for the environment.** The import jobs call services on the public internet through IT's firewall. These hosts must be allowed on HTTPS: `www.ucf.edu`, `jobs.ucf.edu`, `map.ucf.edu`, `pub.orcid.org`, `api.academicanalytics.com`, our Kuali and Slate hosts, Amazon S3 and Amazon Comprehend in `us-east-1`, Sentry, `management.azure.com`, and `*.vault.azure.net`. IT has a request open for the environment, but it was modeled on other apps, so check that these are on it.
- **Values from the VMs.** The credentials in `settings_local.py` on dev's VM (QA's for QA): the S3 keys and `S3_ENV`, Slate, Kuali, Academic Analytics, the Amazon Comprehend keys, and the MySQL connection details.
- **A copy of the MySQL database.** See step 5.

## Step 1: Write down the names and settings

Keep this list open in a text file **outside the repository**. You'll type these values into the portal many times. The file holds names and settings, not secrets — secrets go into Key Vault in step 4.

**Names.** Key Vault names are global and at most 24 characters, and job names at most 32. Adjust them if IT has a naming convention for these resource types.

| What | Dev |
| --- | --- |
| Managed identity | `ucfg-use2-net-searchservice-id-dev` |
| Key Vault | `ucfg-use2-srchsvc-kv-dev` |
| Web app | `search-dev` |
| Jobs | `search-dev-migrate`, `search-dev-import-programs`, and so on |
| Database and role | `searchservice_dev`, `search_dev` |
| Image | `search-service`, tagged with the short commit hash from step 2 |

**Settings** that every container gets, entered as plain values:

| Name | Value |
| --- | --- |
| `DB_ENGINE` | `django.db.backends.postgresql` |
| `DB_NAME` | `searchservice_dev` |
| `DB_USER` | `search_dev` |
| `DB_HOST` | `ucfg-use2-net-searchservice-pdb-001.postgres.database.azure.com` |
| `DB_PORT` | `5432` |
| `ALLOWED_HOSTS` | `search-dev.` followed by the environment's default domain, then `,searchdev.cm.ucf.edu`. The default domain is on the environment's **Overview** page. |
| `USE_S3` | `true` |
| `S3_ENV` | From the VM. If dev points at production's folder, edits on dev change production's images. |
| `AWS_STORAGE_BUCKET_NAME` | `ucf-search-service` |
| `AWS_REGION` | `us-east-1` |
| `KUALI_BASE_URL`, `INSTITUTION_GRID_ID` | From the VM. |
| `SLATE_DEADLINES_ENDPOINT`, `SLATE_DEADLINES_USERNAME`, `SLATE_GUIDS_ENDPOINT`, `SLATE_GUIDS_USERNAME` | From the VM. |
| `AZURE_CLIENT_ID` | Jobs only. The identity's **Client ID**, from its **Overview** page after step 2. |

**Secrets**, each held in Key Vault and referenced by the containers. Leave out any you have no value for — a reference to a secret that doesn't exist stops the container from starting.

| Environment variable | Key Vault secret |
| --- | --- |
| `SECRET_KEY` | `secret-key` |
| `DB_PASSWORD` | `db-password` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `s3-access-key-id`, `s3-secret-access-key` |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` | `comprehend-access-key`, `comprehend-secret-key` |
| `SLATE_DEADLINES_PASSWORD`, `SLATE_GUIDS_PASSWORD` | `slate-deadlines-password`, `slate-guids-password` |
| `KUALI_API_TOKEN` | `kuali-api-token` |
| `ACADEMIC_ANALYTICS_API_KEY` | `academic-analytics-api-key` |
| `SENTRY_DSN` | `sentry-dsn` |

The Comprehend keys are separate from the S3 keys, despite the similar names.

## Step 2: Identity, registry access and image

**Create the identity.** Search for **Managed Identities**, then **Create**. Choose the app resource group, region **East US 2**, and the identity name from step 1. Once it exists, copy its **Client ID** from **Overview** into your list.

**Let it pull from the registry.** Open the registry `ucfguse2ubmmoonshotinfracr01`, then **Access control (IAM)**, **Add**, **Add role assignment**. Choose **AcrPull**, then **Managed identity** on the Members tab, and select the identity. If the assignment is refused, you don't have the right to assign roles there, and nothing can pull the image until you do.

**Build and push the image — in a terminal.** The registry's own build feature, **Tasks**, runs on Azure's machines, which can't reach a registry with public access turned off, so the image is built on your laptop and pushed over the VPN. From the root of the repository:

```sh
git status                  # clean, at the release being deployed
TAG=$(git rev-parse --short HEAD); echo $TAG    # write this down
az acr login -n ucfguse2ubmmoonshotinfracr01    # should end with "Login Succeeded"
docker build --platform linux/amd64 -t ucfguse2ubmmoonshotinfracr01.azurecr.io/search-service:$TAG .
docker push ucfguse2ubmmoonshotinfracr01.azurecr.io/search-service:$TAG
```

A timeout on the login or push means the VPN has no route to the registry, which is the firewall request in "Before you start". `unauthorized` means your account can't push. The `--platform` flag makes an image Azure can run even on an Apple Silicon Mac, where the build is slower because it runs under emulation.

Check in the portal: the registry's **Repositories**, then `search-service`, should list your tag.

## Step 3: PostgreSQL

The server already exists behind a private endpoint IT set up. We don't change its network. We take ownership of the admin password, upgrade it, and create the app's database.

**Find the admin user.** Open the server. **Overview** shows the **Administrator login**. Write it down.

**Reset the admin password**, so we hold it. IT set the current one when they created the server, so tell them before you change it. On **Overview**, choose **Reset password**, and keep the new password somewhere safe until it goes into Key Vault in step 4.

**Check that you can connect — in a terminal**, on the VPN. Replace `ADMIN_USER` with the administrator login:

```sh
psql "host=ucfg-use2-net-searchservice-pdb-001.postgres.database.azure.com dbname=postgres user=ADMIN_USER sslmode=require" -c "select version();"
```

A hang followed by a timeout means the VPN has no route to the database, which is the same firewall request as the registry's.

**Upgrade to PostgreSQL 18.** IT created the server at 17. The app works on both, but CI and local development run 18, and a major upgrade is far easier on an empty server. On **Overview**, choose **Upgrade**, pick **18**, and confirm. The server goes offline for several minutes. We believe 18 is offered as an in-place upgrade for this server, but haven't confirmed it. If 18 isn't in the list, stay on 17 and use `postgres:17` wherever step 5 says `postgres:18`.

**About the tier.** The server is General Purpose, `Standard_D2ds_v5`, because Burstable can't be provisioned in East US 2 or East US right now, and IT has a support case open. By our estimate that's about $130 a month against about $15 for Burstable B1ms. When Burstable becomes available, open **Compute + storage**, choose **Burstable** and **Standard_B1ms**, and save. It restarts the server and keeps the data.

**Leave the server parameters at their defaults.** Under **Server parameters**, `require_secure_transport` should be `ON`, and the time zone UTC. No extensions are needed.

**Create the app's role and database — in a terminal.** The portal's **Databases** page can create a database, but not a role or an owner, so this part is SQL. Dev and QA each get their own pair on this server:

```sh
psql "host=ucfg-use2-net-searchservice-pdb-001.postgres.database.azure.com dbname=postgres user=ADMIN_USER sslmode=require"
```

```sql
CREATE ROLE search_dev LOGIN PASSWORD 'choose-a-strong-password';
-- On PostgreSQL 16 and later, the admin has to be a member of a role to
-- create a database owned by it. Use the administrator login here.
GRANT search_dev TO ADMIN_USER;
CREATE DATABASE searchservice_dev OWNER search_dev ENCODING 'UTF8';
\q
```

For QA, use `search_qa` and `searchservice_qa`. Leave the new database empty; step 5 fills it. The `search_dev` password is `DB_PASSWORD`.

## Step 4: Key Vault and secrets

**Create the vault.** Search for **Key vaults**, then **Create**. Choose the app resource group, the name from step 1, and region **East US 2**. On **Access configuration**, choose **Azure role-based access control**. On **Networking**, leave public access on. Every read and write is still controlled by role, and the environment reaches the vault through the firewall's `*.vault.azure.net` rule. If an Azure Policy refuses a vault with public access, the vault needs a private endpoint, which is a subnet and a DNS record from IT.

**Grant access.** In the vault, open **Access control (IAM)**, then **Add role assignment**, twice:

- **Key Vault Secrets User** for the managed identity, so the app can read secrets.
- **Key Vault Secrets Officer** for yourself, so you can write them.

Role assignments can take a few minutes to apply. If the next part says you're forbidden, wait and retry.

**Add the secrets.** Open **Objects**, then **Secrets**, then **Generate/Import**, once for each row of the secrets table in step 1, with values from the VM. Three need values you make or hold yourself:

- **`secret-key`** is new for each environment. Generate it with `openssl rand -base64 48 | tr -d '\n/+='` in a terminal, or a password manager's generator set to 60 or more characters.
- **`db-password`** is the `search_dev` password from step 3.
- **`postgres-admin-password`** is the admin password from step 3. It isn't referenced by the app. It's here so the team can find it, and only dev's vault needs it.

`sentry-dsn` comes from the project's settings in Sentry.

## Step 5: Load the data

This step runs on your laptop in local containers and can't be done in the portal. The commands are in step 5 of [azure-deployment.md](azure-deployment.md#step-5-load-the-data). Follow them as written, with three substitutions, since that runbook uses shell variables this one doesn't:

- **`$PG_IMAGE`** is `postgres:18`, or `postgres:17` if the upgrade in step 3 wasn't available.
- **`$PG`** is `ucfg-use2-net-searchservice-pdb-001`.
- **`$STAGE`** is `dev`.

In outline: restore the MySQL copy into local MySQL and bring it current, create the schema in local PostgreSQL, copy the data across with pgloader, check row counts, create a superuser, and restore the result into the empty Azure database over the VPN. We tested it on September 25 and November 9 against copies of production, and every table arrived with matching row counts.

To start dev with an empty database instead, skip this step. The migrate job in step 6 builds the empty schema.

## Step 6: The migrate job

**First, check that the environment sends logs somewhere.** Open the environment `ucfg-use2-net-ubmmoonshotinfra-cae-001`, then **Monitoring**, then **Logging options**. It should send to Log Analytics, ideally IT's workspace. If it's set to none, job output is lost. The environment is IT's and shared, so agree any change with them first.

**Create the job.** Search for **Container App Jobs**, then **Create**.

- **Basics.** The app resource group, name `search-dev-migrate`, and the environment `ucfg-use2-net-ubmmoonshotinfra-cae-001`. The list shows environments from other resource groups, so it's there even though it lives in IT's group. Trigger type **Manual**. Replica timeout `7200` seconds, retry limit `0`, parallelism `1`, completion count `1`.
- **Container.** Image source **Azure Container Registry**, the registry `ucfguse2ubmmoonshotinfracr01`, image `search-service`, and your tag. For authentication, choose **Managed identity** and select the identity from step 2. CPU `1`, memory `2Gi`. Command override `python`. Arguments override `manage.py, migrate`.

Create it, and don't run it yet. It has no settings or secrets.

**Add the identity, secrets and settings.** These three pages are the same for every job and for the web app.

1. **Settings, then Identity, then User assigned.** Add the identity from step 2, if the create wizard didn't already.
2. **Settings, then Secrets, then Add**, once per secret in step 1's table. Choose **Key Vault reference**, give it the Key Vault secret name, set the URL to `https://ucfg-use2-srchsvc-kv-dev.vault.azure.net/secrets/` followed by that name, and select the identity.
3. **Application, then Containers, then Edit and deploy.** Select the container, then **Environment variables**. Add every setting from step 1 with source **Manual entry**, including `AZURE_CLIENT_ID`, and every secret with source **Reference a secret**, choosing the matching secret. Save.

A secret whose vault entry is missing, or which the identity can't read, makes the save fail and names the secret. Fix it in the vault and save again.

**Run it.** On **Overview**, choose **Run now**. Then open **Execution history**, wait for **Succeeded**, and open that execution's logs. After step 5, the output should end with `No migrations to apply.` That's the check that the data and the image agree. Lines starting `Applying` mean the image is newer than the database, which is fine if each ends in `OK`.

Two failures are specific to this network. An image pull error means the identity lacks `AcrPull`, or the environment can't reach the registry's private endpoint. A database connection error means the environment's subnet can't reach the database's private endpoint. Your laptop reaching it says nothing about whether the environment can, because they take different routes. Either needs IT to look at the route.

## Step 7: The web app

**Create it.** Search for **Container Apps**, then **Create**.

- **Basics.** The app resource group, name `search-dev`, and the same environment.
- **Container.** The same image, tag and managed identity as the job. CPU `0.5`, memory `1Gi`. No command override.
- **Ingress.** Enabled. Traffic **Accepting traffic from anywhere**, target port `8000`, transport **Auto**. In an internal-only environment, "anywhere" means IT's virtual network, the VPN and campus, not the internet.

**Add the identity, secrets and settings** exactly as for the job in step 6, without `AZURE_CLIENT_ID`.

**Set the scale.** Under **Application**, then **Scale**, set minimum replicas `0` and maximum `2`. Dev then costs almost nothing while nobody uses it, at the price of a short wait on the first request after a quiet stretch. QA should use a minimum of `1`, and production at least `2`.

The address is the **Application Url** on **Overview**. It ends in your `ALLOWED_HOSTS` value, and works only on the VPN until Front Door is in place. Container Apps provides its HTTPS certificate.

## Step 8: Import jobs

Each import is another job, created exactly as in step 6 with a different name and arguments override. For `import-programs`, that's name `search-dev-import-programs` and arguments `manage.py, import-programs`. In dev, keep them **Manual** so we can run each one, time it, and compare its results with the VMs. Start with these two:

| Job | Arguments override |
| --- | --- |
| `search-dev-import-programs` | `manage.py, import-programs` |
| `search-dev-map-units` | `manage.py, map-units` |

Three kinds of import need different things:

- **Database only:** `process-profiles`, `map-units` and `sanitize-unit-names` work as soon as the job exists. `map-units` can fail on PostgreSQL with `MultipleObjectsReturned` until the fix for unordered queries (task 15 in the upgrade plan) merges. That failure is the bug, not the deployment.
- **Outside services:** `import-programs`, `import-tuition`, `import-profiles`, `import-catalog-descriptions`, `import-program-application-deadlines`, `import-slate-guids`, `acad-analytics-import-researchers`, `orcid-meta-import`, `import_location_images`, and the podcast commands need their credentials and an outbound firewall rule for each host they call. A connection timeout in the log almost always means a host isn't on IT's allow list. The log names the host.
- **Files we supply:** `import-cip`, `import-soc`, `import-projection-data`, `import-program-outcome-data`, `import-career-weights`, `import-units` and `import_locations` read data files. We haven't decided how jobs get those files, so leave them out.

Schedules wait until we have an inventory of what runs today. When they come, change a job's trigger type to **Schedule** and give it a cron expression in UTC.

## Step 9: Check that it works

From a browser on the VPN, using the Application Url from step 7:

- **`/healthz`** shows `ok`. It shows `database unavailable` if the app can't reach PostgreSQL. The first request may take a few seconds while dev scales up from zero.
- **`/api/v1/programs/?limit=1`** returns JSON.
- **`/manager/login/`** accepts the superuser from step 5, and a program opens in the admin.
- **A `search-dev-process-profiles` job**, created as in step 8 and run, ends in **Succeeded**. That proves the jobs can write to the database.

If the browser can't find the address at all, the VPN isn't serving DNS for the environment's domain, which is a question for IT. When all four pass, dev is up. Tell the team the address, and that it works only on the VPN for now.

## Deploying a new version

Every release follows the same order. **Migrate first, then the web app, then the jobs.**

1. **Build and push the new commit** in a terminal, exactly as in step 2, and note the new tag.
2. **Migrate.** Open `search-dev-migrate`, then **Containers**, **Edit and deploy**, select the container, and change the tag. Save, then **Run now**, and stop if it doesn't succeed.
3. **The web app.** Open `search-dev`, then **Containers**, **Edit and deploy**, change the tag, and **Create**. That starts a new revision, Container Apps' word for a running version. The old one keeps serving until the new one is up.
4. **Each import job**, the same way as the migrate job. Don't change a job while it's running.

To roll back the web app, open **Revisions and replicas** and send traffic back to the previous revision, or deploy the previous tag. That doesn't undo the migration, which is why we write migrations that work with the previous release's code.

To change a setting, edit the environment variable under **Containers**, **Edit and deploy**, on the web app and on each job that uses it. Update your list from step 1 too.

**One-off commands.** For a quick command such as creating an admin account, open the web app, then **Monitoring**, then **Console**. Choose `/bin/sh` and run `python manage.py createsuperuser`. Load the app's address in a browser first if dev has scaled to zero. Anything longer than a minute or two belongs in a job, because the web app's containers can be replaced at any time.

## When something goes wrong

The web app's logs are under **Monitoring**, then **Log stream**. Switch to **System** to see Azure's side, such as image pulls and startup failures. Each job's logs are under its **Execution history**.

- **Every page returns 400 Bad Request.** The hostname isn't in `ALLOWED_HOSTS`. The log shows `DisallowedHost` with the hostname to add.
- **The app never becomes ready.** Check that the ingress target port is `8000`.
- **`KeyError: 'SECRET_KEY'`, or another variable name, at startup.** A required setting is missing. Compare the container's environment variables with step 1.
- **Image pull fails, or shows `unauthorized`.** The identity lacks `AcrPull` on the registry, or the container's registry authentication isn't set to the managed identity. If both are right, the environment may not reach the registry's private endpoint, which is IT's to check.
- **A secret fails to load.** The identity lacks **Key Vault Secrets User**, the secret's URL has a typo, or the environment can't reach `*.vault.azure.net`.
- **`/healthz` shows `database unavailable`.** Check `DB_HOST`, then the `db-password` secret, then whether the environment's subnet can reach the database.
- **A push or `psql` hangs from your laptop.** The VPN has no route to the private endpoint. Check that you're connected, then raise it with IT.
- **A job stops at exactly two hours.** It hit the replica timeout. Raise it, and note the time it needed.
- **An import ends with "the Front Door purge failed".** The import itself finished. Leave the `FRONT_DOOR_*` settings unset until a Front Door endpoint exists.

If none of these fit, stop and record the full log output.

## Not in this document

- **Production cutover.** Blocked by two open fixes, unordered pagination and case-sensitive `plan_code` filters, and by removing the `teledata` app. It also needs Front Door, single sign-on on the real hostname, and a maintenance window, and should be its own planned event.
- **Production's database.** Production should get its own server, not a third database on dev's, and IT recommends General Purpose or above for it. Its private endpoint is IT's work.
- **Front Door.** It gives the app an address off the VPN: an endpoint on IT's profile with the web app as a Private Link origin, which needs the profile on the Premium tier (shown on the profile's **Overview**). The Private Link connection then has to be approved on the environment, in IT's group. Once it exists, set the `FRONT_DOOR_*` settings on the jobs so imports purge the cache, and give the identity a role that can purge, such as CDN Endpoint Contributor.
- **Single sign-on.** It needs `searchdev.cm.ucf.edu` pointed at Azure through Front Door. Then set `USE_SAML=true`, `SAML_CLIENT_SETTINGS` (as a Key Vault secret) and `SAML_ASSERTION_URL`.
- **Automated deploys.** The GitHub Actions workflow (task 19 in the upgrade plan) hasn't been built, and GitHub's runners can't reach a private registry. It will need a runner inside our network or an ACR dedicated agent pool, both of which need a subnet from IT.
