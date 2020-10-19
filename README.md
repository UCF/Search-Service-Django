# Search Service (Django)

A Django based application that provides a REST API, as well as manual and automated tools for search service data.

## Requirements
- python 3.8+
- pip
- node
- gulp-cli
- angular-cli

## Installation and Setup

1. Create virtual environment for your project: `python3 -m venv projectfolder` and move to the directory `cd projectfolder/`
2. Clone repository into src directory: `git clone git@github.com:UCF/Search-Service-Django.git src` and move to the directory `cd src/`
3. Activate virtual environment: `source ../bin/activate`
4. Install requirements: `pip install -r requirements.txt`
5. Create a gulp config file: `cp gulp-config.tmpl.json gulp-config.json`, then modify as necessary
6. Install the required npm packages: `npm install`
7. Make sure the default artifacts are created: `gulp default`
8. Create a settings_local.py file: `cp settings_local.tmpl.py settings_local.py`, then modify as necessary
9. Run the deployment steps: `python manage.py deploy`. This command is the equivelent of running the following individual commands:
    a. `python manage.py migrate`
    b. `python manage.py collectstatic -l`
10. Run the local server to debug and test: `python manage.py runserver`

## Archimedes Setup

NOTE: to build/test Archimedes, you must set `LOCAL = True` in your settings_local.py.

1. Run `npm install` within the `archimedes` directory.
2. Run `ng build --watch` to view app during development.
3. Run `ng build -c production` to compile angular js for production environment.

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
