# Search Service (Django)

A Django based application that provides a REST API, as well as manual and automated tools for search service data.

## Requirements
- python 3.8+
- pip
- node@14
- gulp-cli
- angular-cli
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

## Archimedes Setup

NOTE: to build/test Archimedes, you must set `LOCAL = True` in your settings_local.py.

1. Run `npm install` within the `archimedes` directory.
2. Run `ng build --watch` to view app during development.
3. Run `ng build -c production` to compile angular js for production environment.

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

## Managing Pip Packages

The `requirements.txt` and `dev-requirements.txt` files in this project are generated using the `pip-tools` package. All package information is tracked within the `pyproject.toml` file and then dependencies are resolved using the following commands:

**Production requirements.txt**
`pip-compile -o requirements.txt pyproject.toml`

**Dev requirements.txt**
`pip-compile --extra=dev --output-file=dev-requirements.txt pyproject.toml`

If you do not already have pip-tools installed, you can install them with the following command: `pip install pip-tools`.
