Django Nomination
=================

[![Build Status](https://travis-ci.org/unt-libraries/django-nomination.svg?branch=master)](https://travis-ci.org/unt-libraries/django-nomination)
[![codecov.io](https://codecov.io/github/unt-libraries/django-nomination/coverage.svg?branch=master)](https://codecov.io/github/unt-libraries/django-nomination?branch=master)


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

* Python 2.7
* Django 1.6


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
            url(r'^admin/', include(admin.site.urls)),
            url(r'^nomination/', include('nomination.urls')),
        ]
    ```

4. Sync the database.
    ```sh
        $ python manage.py syncdb
    ```


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
        $ docker-compose up -d
        # Use 'docker-compose stop' to stop the container.
    ```
    At this point you should be able to access your local instance of the site by visiting `<dockerhost>:8000/nomination/`.

5. Create a superuser for access to the admin sites.
    ```sh
        $ docker-compose run --rm web python manage.py createsuperuser
    ```

6. If desired, run the tests.
    ```sh
        $ docker-compose run --rm web tox
    ```


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