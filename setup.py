#! /usr/bin/env python
from setuptools import setup

setup(
    name='django-nomination',
    version='0.9.0',
    packages=['nomination'],
    description='',
    long_description='See the home page for more information.',
    include_package_data=True,
    install_requires=[
        'simplejson>=3.8.1',
        'django-markup-deprecated>=0.0.3',
        'markdown>=2.6.5'
    ],
    zip_safe=False,
    url='https://github.com/unt-libraries/django-nomination',
    author='University of North Texas Libraries',
    author_email='mark.phillips@unt.edu',
    license='BSD',
    keywords=[
        'django',
        'app',
        'UNT',
        'url',
        'surt',
        'nomination',
        'web archiving'
    ],
    classifiers=[
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Framework :: Django :: 1.6',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ]
)