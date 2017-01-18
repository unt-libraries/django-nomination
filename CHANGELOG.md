Change Log
==========

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
