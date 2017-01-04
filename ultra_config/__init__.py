"""
A library for managing configuration through
multiple mechanisms.  It additionally allows
for global, lazy configuration for a given
python application via the ``GlobalConfig``
class.  It also makes it very easy to override
configuration for testing purposes.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import wraps

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
import json

from insensitive_dict import CaseInsensitiveDict
from env_config import get_envvar_configuration

__author__ = 'Tim Martin'
__email__ = 'tim@timmartin.me'
__version__ = '0.5.0'


def load_python_module_settings(module, ignore_prefix='_'):
    """
    Loads all items from a python module as
    potential configuration.  The name of the variable
    will be the key in the dictionary.

    .. code-block:: python

        from ultra_config import load_python_module_settings
        import mymodule

        config = load_python_module_settings(mymodule)

    :param object module: A python module object
    :param unicode ignore_prefix: Any variable in the module
        that starts with this prefix will be ignored.
    :return: The items from the module as a dictionary
    :rtype: dict
    """
    items = {}
    for key, value in module.__dict__.items():
        if not (key.startswith(ignore_prefix)):
            items[key] = value
    return items


def load_python_object_settings(obj, ignore_prefix='_'):
    """
    Loads the attributes on an object as a configuration
    object.  By default it will ignore all attributes prefixed
    with a ``'_'``

    .. code-block:: python

        class MyObj(object):
            def __init__(self):
                self.x = 1

        my_obj = MyObj()
        config = load_python_object_settings(my_obj)
        assert config['x'] == 1

    :param object obj:
    :return: A configuration dictionary
    :rtype: dict
    """
    return load_python_module_settings(obj, ignore_prefix=ignore_prefix)


def load_dict_settings(dictionary):
    """
    A simple wrapper that just copies the dictionary

    :param dict dictionary:
    :return: A configuration dictionary
    :rtype: dict
    """
    return dictionary.copy()


def load_configparser_settings(filename):
    """
    Loads a ``*.ini`` style file as configuration.
    It returns a dictionary of dictionaries with
    each section getting its own dictionary

    :param unicode filename: The name of the file
        to load as configuration
    :return: A dictionary of dictionaries with
        the key of the parent representing a section
        and the value being a dictionary of the configuration
        for that section
    :rtype: dict
    """
    items = {}
    config_parser = ConfigParser()
    config_parser.read(filename)
    for section_key in config_parser.sections():
        items[section_key] = {}
        for option_key in config_parser.options(section_key):
            items[section_key][option_key] = config_parser.get(section_key, option_key)
    return items


def load_json_file_settings(filename):
    """
    Loads a json file as configuration
    The json file should contain a JSON
    object and not a JSON array, string or other
    value

    :param unicode filename: The name of
        the json file to load
    :return: A dictionary of the values from
        the json file
    :rtype: dict
    """
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
        """
        :param list loaders: A list of configuration loaders
            Each loader should be a tuple with three items
            a function that loads the config, a list of arguments
            to pass to the function and a dictionary of the keyword
            arguments to pass to the function.  Each should be
            tuple(``function``, ``list``, ``dict``)
        :param list[unicode] required: A list keys that are required
            for the configuration.
        """
        self.required = required or []
        super(UltraConfig, self).__init__()
        self._loaders = list(loaders)

    def load(self):
        """
        Loads all of the configuration as specified
        by the ``loaders``
        """
        for loader in self._loaders:
            config_loader_func = loader[0]
            args = loader[1] if len(loader) > 1 else []
            kwargs = loader[2] if len(loader) > 2 else {}
            items = config_loader_func(*args, **kwargs)
            self.update(items)

    def validate(self):
        """
        Ensures that all required configuration items
        are available in the configuration.

        Raises a ``MissingConfigurationException`` if there
        is any missing configuration

        :raises: MissingConfigurationException
        """
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
    config = {}

    @classmethod
    def load(cls, *args, **kwargs):
        """
        Loads the global configuration, replacing
        existing configuration if it's already set.
        Takes the same parameters as ``simple_config``
        """
        cls.config = simple_config(*args, **kwargs)

    @classmethod
    def inject(cls, *inject_args, **inject_kwargs):
        """
        Inject arguments and keyword arguments from
        configuration lazily.  Keyword arguments passed
        into the function that conflict with the injected
        arguments will not be overridden.

        .. code-block:: simple

            fron ultra_config import GlobalConfig

            @GlobalConfig.inject('SETTING1', keyword='SETTING2')
            def myfunc(arg, keyword=None):
                print('arg: {0}, keyword: {1}', arg, keyword)

            myfunc()
            # prints "arg: 1, keyword: 2

            myfunc(keyword="don't inject")
            # prints "arg: 1, keyword: don't inject"

        :param inject_args:
        :param inject_kwargs:
        :return:
        """
        def decorator(func):
            """The actual decorator"""
            @wraps(func)
            def wrapper(*args, **kwargs):
                """Wrapper for actual function"""
                extra_args = [cls.config[name] for name in inject_args]
                all_args = list(args) + list(extra_args)
                for key, value in inject_kwargs.items():
                    if key not in kwargs:
                        kwargs[key] = cls.config[value]
                return func(*all_args, **kwargs)
            return wrapper
        return decorator
