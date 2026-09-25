# Search Service (Django)

A Django based application that provides a REST API, as well as manual and automated tools for search service data.

## Requirements
- python 3.8+
- pip
- node@14
- gulp-cli
- Fontawesome 6+ pro

## Installation and Setup

1. Create virtual environment for your project: `python3 -m venv projectfolder` and move to the directory `cd projectfolder/`
2. Clone repository into src directory: `git clone git@github.com:UCF/Search-Service-Django.git src` and move to the directory `cd src/`
3. Activate virtual environment: `source ../bin/activate`
4. Create a .npmrc file in the home directory. Copy the script from template.npmrc and paste it into .npmrc. Then, replace authToken=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX with the Pro Token purchased from FA6.
5. Install requirements: `pip install -r requirements.txt`
6. Create a gulp config file: `cp gulp-config.tmpl.json gulp-config.json`, then modify as necessary
7. Install the required npm packages: `npm install`
8. Make sure the default artifacts are created: `gulp default`
9. Create a settings_local.py file: `cp settings_local.tmpl.py settings_local.py`, then modify to add API keys and the like.
    - Note: during this step, you _should not modify_ `STATIC_ROOT` or `STATICFILES_DIRS`.
10. Run the deployment steps: `python manage.py deploy`. This command is the equivelent of running the following individual commands:
    a. `python manage.py migrate`
    b. `python manage.py collectstatic -l`
11. Once deployment steps have run successfully, comment out `STATIC_ROOT` and add a static root path to `STATICFILES_DIRS` in settings_local.py.
12. Create a superuser to access the Django admin with: `python manage.py createsuperuser`
13. Optionally, load fixtures: `python manage.py loaddata fixture-name`. Fixtures, if available, are included per-app in a `fixtures` directory.
    - Note: if loading in fixtures for Programs, make sure the `colleges` fixture is loaded _before_ loading the `collegeoverrides` fixture.
14. Run the local server to debug and test: `python manage.py runserver`

## Running in a Container

The `Dockerfile` builds the image we deploy, and `compose.yaml` runs it locally against PostgreSQL. You need Docker (or Podman) with Compose.

1. Build and start the app and database: `docker compose up --build`
2. In another terminal, run the migrations: `docker compose run --rm web python manage.py migrate`
3. Create a superuser: `docker compose run --rm web python manage.py createsuperuser`

The API is then at http://localhost:8000/api/v1/. Settings come from `settings_local.tmpl.py` plus the environment variables read by `docker/env-settings.py`; `compose.yaml` sets local values for them.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY`, `DB_ENGINE`, `DB_NAME` | Required. |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Database connection. |
| `DEBUG`, `ALLOWED_HOSTS` | `DEBUG=true` for local development; `ALLOWED_HOSTS` is comma-separated. |
| `USE_S3`, `S3_ENV`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` | Media uploads to S3. |
| `SLATE_DEADLINES_ENDPOINT`, `SLATE_DEADLINES_USERNAME`, `SLATE_DEADLINES_PASSWORD`, and the same three for `SLATE_GUIDS_` | Graduate Studies' Slate. |
| `KUALI_BASE_URL`, `KUALI_API_TOKEN`, `ACADEMIC_ANALYTICS_API_KEY`, `INSTITUTION_GRID_ID` | Import credentials. |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION` | Amazon Comprehend, used by `import-catalog-descriptions` unless it runs with `--fast`. |
| `USE_SAML`, `SAML_CLIENT_SETTINGS`, `SAML_ASSERTION_URL` | Single sign-on. `SAML_CLIENT_SETTINGS` is the pysaml2 client configuration as JSON. |
| `SENTRY_DSN` | Error reporting, read by raven directly. |
| `FRONT_DOOR_SUBSCRIPTION_ID`, `FRONT_DOOR_RESOURCE_GROUP`, `FRONT_DOOR_PROFILE`, `FRONT_DOOR_ENDPOINT`, `FRONT_DOOR_DOMAINS`, `AZURE_CLIENT_ID` | The Front Door endpoint to purge after imports, and the user-assigned managed identity to purge as. Unset, purging does nothing. |

Each import purges the API paths it changes from Front Door when it finishes. Add `--no-purge` to skip that, for example when running several imports in a row and purging once at the end with `python manage.py purge-cache '/api/v1/*'`.

The container trusts the `X-Forwarded-Proto` and `X-Forwarded-Host` headers set by App Service and Front Door, and marks cookies secure unless `DEBUG` is on.

The front-end assets in `static/` are compiled with gulp and committed, so the image doesn't build them. `collectstatic` runs when the image is built, and WhiteNoise serves everything in `static/` from the container.

## DEV Package Installation

There are some additional libraries necessary to run some of the management command scripts not meant to be run on a server. For example, the `manage.py generate-career-weights` command uses the `spacy` package and its associated library of words, which can take up around .5GB of space, so we want to avoid installing that on servers.

The install these additional packages, run the following: `pip install -r dev-requirements.txt`.

## Installation Notes
The pip dependency `lxml` requires some additional libraries to be installed on the server the application is running on. You can run the following commands to install:

*Ubuntu*
```
sudo apt-get install -y libxml2-dev libxslt1-dev
```

*RHEL*
```
sudo yum install libxml2 libxml2-devel libxml2-python libxslt libxslt-devel
```

## Managing Packages

Dependencies are managed with [uv](https://docs.astral.sh/uv/). All package information is tracked within the `pyproject.toml` file, and the resolved versions are locked in `uv.lock`. The `.python-version` file pins the Python version to match production.

To set up a local environment from the lock file:
`uv sync` (add `--extra dev` for the dev packages)

To add or upgrade a package, edit `pyproject.toml` or use `uv add`/`uv lock --upgrade-package <name>`, then regenerate the requirements files the servers install from:

**Production requirements.txt**
`uv export --frozen --no-hashes --no-emit-project -o requirements.txt`

**Dev requirements.txt**
`uv export --frozen --no-hashes --no-emit-project --extra dev -o dev-requirements.txt`

Commit `pyproject.toml`, `uv.lock`, and both requirements files together.

## Running Tests

Run the test suite with `python manage.py test`.
