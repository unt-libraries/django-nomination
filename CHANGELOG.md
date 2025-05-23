Change Log
==========


5.0.0
-----

* Upgraded to Django 4.2.
* Fixed nominating URLs of length 255-300 chars by ensuring `value` is big enough to hold the URL's SURT value. [#114](https://github.com/unt-libraries/django-nomination/issues/114)
* Fixed browsing from listing page to top-level domain SURT URLs. [#115](https://github.com/unt-libraries/django-nomination/issues/115)
* Fixed links in URL lookup search results that needed encoding. [#118](https://github.com/unt-libraries/django-nomination/issues/118)
* Converted fielded_batch_ingest.py script to a Django management command and improved speed.
* Updated info about bookmarklets. [#120](https://github.com/unt-libraries/django-nomination/issues/120)


4.0.0
-----

* Upgraded to Django 4.1.
* Dropped support for Django 2.2.
* Dropped support for Python 3.7.
* Added support for Python 3.10.


3.0.0
-----

* Upgraded to Django 2.2.
* Dropped support to Django 1.11 and versions below.
* Improved a URL regex to only accept numbers for a numerical ID.
* Used get_object_or_404 where appropriate to mitigate server errors.
* Fixed a flake8 indentation error.
* Upgraded compatibility to  Python 3.7
* Removed compatibility with Django 1.10
* Removed compatibility with Python 2
* Added slim-select for improved select inputs
* Prevent duplicates in url_report if a surt is duplicated in the data.
* nominator_email is made unique.
* Fixed admin links.
* Used get_or_create and get_object_or_404 where appropriate.
* Replaced Travis with GitHub Actions.
* Added support for Python 3.8-3.9.


2.0.0
-----

* Upgraded compatibility to Django 1.10 and 1.11
* Removed compatibility with Django < 1.10
* Made code compliant with PEP-8 style rules.


1.1.0
-----

* Removed assumptions that nominations will be for URLs with http scheme.[#67](https://github.com/unt-libraries/django-nomination/issues/67)
* Adjusted partial search to be scheme agnostic.
* Added scheme agnostic SURT browsing.[#80](https://github.com/unt-libraries/django-nomination/issues/80)
* Modified search by URL to allow alternate schemes when exact match is not available.
* Moved compiling of regular expressions outside of loops.[#38](https://github.com/unt-libraries/django-nomination/issues/38)
* Removed three unreachable branches in create_json_browse(). [#26](https://github.com/unt-libraries/django-nomination/issues/26)
* Removed 'except' branch in url_lookup view that never catches anything. [#31](https://github.com/unt-libraries/django-nomination/issues/31)


1.0.3
-----

* Fixed incorrect URL pattern matching for nominated URLs ending in strings matching other
URL patterns. [#85](https://github.com/unt-libraries/django-nomination/issues/85)
* Fixed feeds being excessively slow due to making too many queries.
* Added double slashes being stripped from ftp nominations.
* Fixed removal of 's' for ftps or https nominations.


1.0.2
-----

* Fixed removal of double slash in https URLs when going from search to nomination form.
* Added link to fielded_batch_ingest.py documentation.


1.0.1
-----

* Moved input help text location (now immediately below input label for all inputs).
* Updated docker-compose.yml to use version 2 syntax.
* Added static file collection location to settings.


1.0.0
-----

* Initial release.
