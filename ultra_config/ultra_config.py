# -*- coding: utf-8 -*-
from configparser import ConfigParser
import json

from CaseInsensitiveDict import CaseInsensitiveDict
from env_config import get_envvar_configuration

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
    for key, value in config_parser.items():
        items[key] = value
    return items


def load_json_file_settings(filename):
    with open(filename, mode='rb') as f:
        return json.load(f)


class UltraConfig(CaseInsensitiveDict):
    def __init__(self, *loaders):
        self._loaders = list(loaders)
        self._data = {}

    def load(self):
        for loader in self._loaders:
            config_loader_func = loader[0]
            args = loader[1] if len(loader) > 1 else []
            kwargs = loader[2] if len(loader) > 2 else {}
            items = config_loader_func(*args, **kwargs)
            self.update(items)


def simple_config(default_settings=None, json_file=None, ini_file=None, env_var_prefix=None, overrides=None):
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
        loaders.append([load_python_module_settings, default_settings])
    if json_file:
        loaders.append([load_json_file_settings, json_file])
    if ini_file:
        loaders.append([load_configparser_settings, ini_file])
    if env_var_prefix:
        loaders.append([get_envvar_configuration, env_var_prefix])
    if overrides:
        loaders.append([load_dict_settings, overrides])

    config = UltraConfig(*loaders)
    config.load()
    return config



