============
ultra-config
============


.. image:: https://img.shields.io/pypi/v/ultra_config.svg
        :target: https://pypi.python.org/pypi/ultra_config

.. image:: https://travis-ci.org/timmartin19/ultra-config.svg?branch=master
        :target: https://travis-ci.org/timmartin19/ultra-config

.. image:: https://readthedocs.org/projects/ultra-config/badge/?version=latest
        :target: http://ultra-config.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/timmmartin19/ultra_config/shield.svg
     :target: https://pyup.io/repos/github/timmmartin19/ultra_config/
     :alt: Updates


An extendable configuration that enables you to configure your application via python modules, config files, environment variables and more!


* Free software: MIT license
* Documentation: https://ultra-config.readthedocs.io.


Installation
------------

.. code-block:: bash

    pip install ultra-config


Features
--------

* Load configuration from a variety of sources including environment variables, json files, ini files, and python objects
* Easily extend with your own configuration mechanisms
* Offers a global configuration object for you application
* Easily inject configuration into functions with the ability to override them for testing
* Ability to fail fast if missing configuration

Examples
--------

global configuration
""""""""""""""""""""

.. code-block:: python

    from ultra_config import GlobalConfig

    # Loads all env variables that begin with MY_APP, configuration
    # from a json file and a custom override
    GlobalConfig.load(env_var_prefix='MY_APP',
                      json_file='/opt/my_app/config.json',
                      overrides={'MY_VAR': 'some_val'})

    @GlobalConfig.inject('MY_VAR', value='OTHER_VAR')
    def my_func(arg1, value=None):
        print(arg1)
        print(value)

    my_func()
    # Prints the value of MY_VAR and OTHER_VAR

    my_func(value='custom')
    # prints the value of MY_VAR and then prints the "custom" since we explicitly passed that in

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

