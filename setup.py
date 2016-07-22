#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'CaseInsensitiveDict',
    'Click>=6.0',
    'py-env-config'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='ultra_config',
    version='0.1.3',
    description="An extendable configuration that enables you to configure your application via python modules, config files, environment variables and more!",
    long_description=readme + '\n\n' + history,
    author="Tim Martin",
    author_email='tim@timmartin.me',
    url='https://github.com/timmmartin19/ultra_config',
    packages=[
        'ultra_config',
    ],
    package_dir={'ultra_config':
                 'ultra_config'},
    entry_points={
        'console_scripts': [
            'ultra_config=ultra_config.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='ultra_config',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='ultra_config_tests',
    tests_require=test_requirements
)
