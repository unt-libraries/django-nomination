Django Nomination
=================

[![Build Status](https://github.com/unt-libraries/django-nomination/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/unt-libraries/django-nomination/actions)


About
-----

This app is used to collect URLs for projects. Projects can declare certain
metadata fields to be included in the information provided with each URL
nomination. The URLs themselves are collected through nominations, which are
entered by individuals who believe that URL to be somehow related to the
project. Each project then maintains a list of URLs which are scored based on
whether nominators deem those URLs to be in-scope or out-of-scope for the
current project. Reports are automatically generated for each project and show
overall URL scores, how many nominations each has received, which URLs were
nominated by person or institution, etc.

UNT Libraries developed this app to determine which URLs to harvest in web
crawls for certain archival projects.


Requirements
------------

* Python 3.8-3.10
* Django 4.2


Installation
------------

1. Install from GitHub.
    ```sh
        $ pip install git+git://github.com/unt-libraries/django-nomination.git
    ```

2. Add nomination to INSTALLED_APPS.
    ```python
        INSTALLED_APPS = (
            'django.contrib.admin',
            'nomination',
        )
    ```

3. Add the URL patterns.
    ```python
        urlpatterns = [
            path('admin/', admin.site.urls),
            path('nomination/', include('nomination.urls')),
        ]
    ```

4. Run the migrations.
    ```sh
        $ python manage.py migrate
    ```

5. Change the contact information shown in the app by overriding the `contact_info.html` template.


Developing
----------

1. [Install Docker](http://docs.docker.com/installation/).

2. Install Docker Compose.
    ```sh
        $ pip install docker-compose
    ```

3. Clone the repository.
    ```sh
        $ git clone https://github.com/unt-libraries/django-nomination
    ```

4. Start the container as a daemon.
    ```sh
        $ docker compose up -d
        # Use 'docker compose stop' to stop the container.
    ```
    At this point you should be able to access your local instance of the site by visiting `<dockerhost>:8000/nomination/`.

5. Create a superuser for access to the admin sites.
    ```sh
        $ docker compose run --rm web python manage.py createsuperuser
    ```

6. If desired, run the tests.
    ```sh
        $ docker compose run --rm web tox
    ```

If you are on RHEL, your installation and commands may be different.

1. [Install or Enable Podman](https://podman.io/getting-started/installation).

2. [Install Podman Compose](https://github.com/containers/podman-compose).
    ```sh
        $ sudo dnf install podman-compose
    ```

3. Clone the repository.
    ```sh
        $ git clone https://github.com/unt-libraries/django-nomination
    ```

4. If you have SELinux, you may need to temporarily add `:Z` to the web volume in the docker-compose.yml. It will look like `.:/app/:Z`.

5. Start the container as a daemon.
    ```sh
        $ sudo podman-compose up -d
        # Use 'sudo podman-compose stop' to stop the container.
    ```
    At this point you should be able to access your local instance of the site by visiting `<dockerhost>:8000/nomination/`.

6. Create a superuser for access to the admin sites.
    ```sh
        $ sudo podman-compose run --rm web python manage.py createsuperuser
    ```

7. If desired, run the tests.
    ```sh
        $ sudo podman-compose run --rm web tox
    ```

Batch Ingest Management Command
-------------------------------

For bulk loading of URL nominations into a Nomination Tool instance,
there is a `fielded_batch_ingest` management command. Input file formats
include:

* text file - one URL per line
* CSV - lines contain a `url` field as well as additional arbitrary metadata fields that must be named on the first line (e.g. the first line of the CSV might look like `url,Title,List_Name`)
* pickled dictionary - serialized Python object in pickle format. This allows multivalued attributes that can be stored in a Python dictionary as lists.

To view details on this bulk loading tool, run:
```sh
    $ python manage.py fielded_batch_ingest -h
```

For example, to load a CSV file:
```sh
    $ python manage.py fielded_batch_ingest tests/data/test.csv --nominator 2 --project project1 --csv
```


Helper Scripts
--------------

There are two scripts made available with this app that can help with batch
uploading of project information, such as project metadata and URL nominations.
They are located in the user_scripts subdirectory and are intended to be run
from the machine serving the app. They require access to the settings file used
by the Django project hosting the app. If you are serving the app using a virtual
environment, the script will need to be run from within that same environment.
The scripts are well-commented and designed to be used from the
command-line. Invoke them with the `-h` flag to see their help documentation.


License
-------

See LICENSE.txt.


Contributors
------------

* Brandon Fredericks
* [Lauren Ko](https://github.com/ldko)
* [Mark Phillips](https://github.com/vphill)
* [Joey Liechty](https://github.com/yeahdef)
* [Gio Gottardi](https://github.com/somexpert)
* [Jason Ellis](https://github.com/jason-ellis)
* [Madhulika Bayyavarapu](https://github.com/madhulika95b)
* [Gracie Flores-Hays](https://github.com/gracieflores)
