"""
Contains various small utilities for handling
encrypted secrets and loading them appropriately
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import warnings

from ultra_config import UltraConfig

LOG = logging.getLogger(__name__)


def decrypt(config, decrypter, secrets_config_key='SECRETS', secrets_list=None):
    """
    Takes a config object and decrypts the values of the keys
    specified in the configuration itself or via the ``secrets_list``
    parameter.  Please note that it modifies the config object!

    By default the ``'SECRETS'`` configuration parameter
    is used to determine which keys need to be decrypted.
    It should be a list of unicode keys.  You can override
    the configuration parameter that holds the keys with
    ``secrets_config_key='MY_SECRETS'``.   Additionally,
    you can set it to ``None`` and it will not attempt to
    load the keys from the configuration.

    If you wish to manually set a list of keys to decrypt
    (e.g. if you set ``secrets_config_key==None``, then
    you can manually pass in a set of keys via
    ``secrets_list=['API_SECRET', 'DB_PASSWORD']``.

    :param UltraConfig config: The configuration object
        with the secrets to decrypt
    :param function decrypter: The function that takes an
        encrypted object and returns the decrypted version
    :param unicode|None secrets_config_key: The configuration key
        that contains a list of configuration keys that need
        to be decrypted
    :param list[unicode] secrets_list: A list of configuration
        keys the need to be decrypted
    :rtype: NoneType
    """
    keys = []
    if secrets_config_key is not None:
        configuration_keys = config.get(secrets_config_key)
        if configuration_keys is None:
            warnings.warn('ultra-config was unable to find any configuration for '
                          '{0}.  Please set {0}=[] in your configuration or pass '
                          '`secrets_config_key=None` if you wish to manually set '
                          'the configuration keys to decrypt'.format(secrets_config_key))
            configuration_keys = []
        keys.extend(configuration_keys)
    secrets_list = secrets_list or []
    keys.extend(secrets_list)

    for key in keys:
        config[key] = decrypter(config.get(key))
