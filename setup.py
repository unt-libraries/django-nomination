#! /usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-nomination',
    version='2.0.0',
    packages=find_packages(exclude=['tests*']),
    description='',
    long_description='See the home page for more information.',
    include_package_data=True,
    install_requires=[
        'markdown>=3.0.1',
        'django-widget-tweaks>=1.4.1',
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
        'Framework :: Django :: 2.2',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ]
)
