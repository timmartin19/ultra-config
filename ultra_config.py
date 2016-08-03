# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
import json

from insensitive_dict import CaseInsensitiveDict
from env_config import get_envvar_configuration

__author__ = 'Tim Martin'
__email__ = 'tim@timmartin.me'
__version__ = '0.4.0'


def load_python_module_settings(module):
    items = {}
    for key, value in module.__dict__.items():
        if not (key.startswith('__') and key.endswith('__')):
            items[key] = value
    return items


def load_python_object_settings(obj):
    return load_python_module_settings(obj)


def load_dict_settings(dictionary):
    return dictionary.copy()


def load_configparser_settings(filename):
    items = {}
    config_parser = ConfigParser()
    config_parser.read(filename)
    for section_key in config_parser.sections():
        items[section_key] = {}
        for option_key in config_parser.options(section_key):
            items[section_key][option_key] = config_parser.get(section_key, option_key)
    return items


def load_json_file_settings(filename):
    with open(filename, mode='r') as f:
        return json.load(f)


class MissingConfigurationException(ValueError):
    """
    Raised when a require configuration
    parameter is missing
    """


class UltraConfig(CaseInsensitiveDict):
    """
    A case insensitive dictionary like object
    that allows for loading configuration
    using a multitude of mechanisms
    """
    def __init__(self, loaders, required=None):
        self.required = required or []
        super(UltraConfig, self).__init__()
        self._loaders = list(loaders)

    def load(self):
        for loader in self._loaders:
            config_loader_func = loader[0]
            args = loader[1] if len(loader) > 1 else []
            kwargs = loader[2] if len(loader) > 2 else {}
            items = config_loader_func(*args, **kwargs)
            self.update(items)

    def validate(self):
        missing_items = []
        for item in self.required:
            if item not in self:
                missing_items.append(item)
        if len(missing_items) > 0:
            required_string = ', '.join(['"{0}"'.format(item) for item in missing_items])
            raise MissingConfigurationException('Missing required items: {0}'.format(required_string))


def simple_config(default_settings=None,
                  json_file=None,
                  ini_file=None,
                  env_var_prefix=None,
                  overrides=None,
                  required=None):
    """
    Loads configuration in the following order
    * default_settings python module object
    * json_file
    * ini_file
    * environment variables starting with env_var_prefix
    * overrides dict

    Configuration from latter ones will override previous ones

    :param module default_settings:
    :param unicode json_file:
    :param unicode ini_file:
    :param unicode env_var_prefix:
    :param dict overrides:
    :return: UltraConfig
    """
    loaders = []
    if default_settings:
        loaders.append([load_python_module_settings, [default_settings]])
    if json_file:
        loaders.append([load_json_file_settings, [json_file]])
    if ini_file:
        loaders.append([load_configparser_settings, [ini_file]])
    if env_var_prefix:
        loaders.append([get_envvar_configuration, [env_var_prefix]])
    if overrides:
        loaders.append([load_dict_settings, [overrides]])

    config = UltraConfig(loaders, required=required)
    config.load()
    config.validate()
    return config


class GlobalConfig(object):
    """
    A global configuration object.  This class
    is not designed to be instantiated but rather
    just as a container.

    .. doctest:: globalconfig

        >>> from ultra_config import GlobalConfig
        >>> GlobalConfig.load(env_var_prefix='my_app', overrides={'my_setting': 1})
        >>> assert GlobalConfig.config['my_setting'] == 1
    """
    config = None

    @classmethod
    def load(cls, *args, **kwargs):
        """
        Loads the global configuration, replacing
        existing configuration if it's already set.
        Takes the same parameters as ``simple_config``
        """
        cls.config = simple_config(*args, **kwargs)
