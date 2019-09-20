#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.rst", "r") as fh:
    readme = fh.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'dataclasses>=0.6']

setup_requirements = []

test_requirements = []

setup(
    author="Yang Liu",
    author_email='yliu0@uw.edu',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Author and execute multiverse analysis",
    entry_points={
        'console_scripts': [
            'boba=boba.cli:main',
        ],
    },
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='multiverse analysis',
    name='boba',
    packages=find_packages(include=['boba']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/uwdata/multiverse-spec',
    version='0.1.2',
    zip_safe=False,
)
