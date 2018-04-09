# Search Service (Django)

A Django based application that provides a REST API, as well as manual and automated tools for search service data.

## Installation and Setup

1. Install virtual environment: `pip install virtualenv`
2. Create virtual environment for your project: `virtualenv projectfolder` and move to the directory `cd projectfolder/`
3. Clone repository into src directory: `git clone git@github.com:UCF/Search-Service-Django.git src` and move to the directory `cd src/`
4. Activate virtual environment: `source ../bin/activate`
5. Install requirements: `pip install -r requirements.txt`
6. Install the required npm packages: `npm install`
7. Make sure the default artifacts are created: `gulp default`
8. Run the deployment steps: `python manage.py deploy`. This command is the equivelent of running the following individual commands:
    a. `python manage.py migrate`
    c. `python manage.py collectstatic -l`
9. Run the local server to debug and test: `python manage.py runserver`

