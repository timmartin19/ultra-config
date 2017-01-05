from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import json
from json.decoder import JSONDecodeError
import logging

LOG = logging.getLogger(__name__)

try:
    unicode_type = unicode
except NameError:
    unicode_type = str


def create_kms_decrypter(client, decode=True, **kwargs):
    """
    Returns a decrypter function designed to be
    used in conjunction with ``ultra_config.secrets:decrypt``.

    The returned function uses AWS KMS as the decryption mechanism.
    It requires the AWS IAM permission Allow on ``kms:Decrypt``

    :param client: A kms client e.g. ``boto3.client('kms')``
    :param bool decode: If True, decode as utf-8 automatically
    :param dict kwargs: Additional arguments to be passed to the
        ``client.decrypt`` function (e.g. GrantToken or EncryptionContext).
    :return: The decrypter function
    """
    def kms_decrypter(value):
        """
        A decrypter function to be used with ``ultra_config.secrets:decrypt``
        that uses AWS KMS as the decryption mechanism

        :param unicode value: The value to decrypt
        :return: The decrypted value
        :rtype: unicode
        """
        if isinstance(value, unicode_type):
            value = value.encode('utf-8')
        value = base64.b64decode(value)
        resp = client.decrypt(CiphertextBlob=value, **kwargs)
        if decode:
            return resp['Plaintext'].decode('utf-8')
        return resp['Plaintext']
    return kms_decrypter


def encrypt_kms(client, key_id, value, **kwargs):
    """
    Encrypts and appropriate encodes the given value
    for use by the function returned by ``create_kms_decrypter``.

    This is intended only as a helper for setting the configuration
    in the first place.

    :param client: a boto3 kms client e.g. ``boto3.client('kms')``
    :param unicode key_id: The alias or ARN of the KMS key
        to use for encryption
    :param unicode value: The value to encrypt
    :param kwargs: Additional arguments to pass to the
        encrypt call
    :return: The encrypted value
    :rtype: unicode
    """
    if isinstance(value, unicode_type):
        value = value.encode('utf-8')
    resp = client.encrypt(KeyId=key_id, Plaintext=value, **kwargs)
    encrypted = resp['CiphertextBlob']
    encrypted = base64.b64encode(encrypted)
    return encrypted.decode('utf-8')


def create_kms_encrypter(client, key_id, **kwargs):
    """
    Creates a function that can be used for re-encrypted
    configuration

    :param client: a boto3 kms client
    :param unicode key_id: The alias or arn of the KMS key
        to use for encryption
    :param dict kwargs: Extra arguments to pass to the
        kms client encryption call
    :return: A function that takes an unencrypted value
        and returns the encrypted value
    :rtype: function
    """
    def encrypter(value):
        return encrypt_kms(client, key_id, value, **kwargs)
    return encrypter


def load_task_definition_settings(data, prefix=None, container=0, load_as_json=True):
    """
    A loader that loads the environment variables from a
    task definition file as dictionary of keys and values.

    Please note that this is not intended for production
    use and is just a helpful mechanism to determine which
    configuration parameters will be loaded by the environment
    variable loader

    :param list[dict] data: The task definition.  Please
        note that only one of the container's environment
        variables are loaded
    :param unicode prefix: The prefix for environment variables
        If the name of the env var does not start with the prefix
        it's ignored other wise the configuration is added and
        the prefix is stripped
    :param int container: The index of the container whose
        configuration should be loaded
    :param bool load_as_json: Indicates whether the
        configuration values should be loaded as json
    :return: The loaded configuration
    :rtype: dict
    """
    env_vars = data[container]['environment']

    config = {}
    for env_var in env_vars:
        key = _strip_prefix(env_var['name'], prefix)
        if not key:
            continue

        if load_as_json:
            try:
                config[key] = json.loads(env_var['value'])
            except JSONDecodeError:  # raw strings
                config[key] = env_var['value']
        else:
            config[key] = env_var['value']
    return config


def _convert_to_task_definition_environment(config, prefix=None, dump_as_json=True):
    """
    Converts configuration back into the format that a task definition uses
    """
    env_vars = []
    for key, value in config.items():
        if dump_as_json and not isinstance(value, str):
            value = json.dumps(value)
        if prefix is not None:
            key = '{0}_{1}'.format(prefix, key)
        env_vars.append({'name': key, 'value': value})
    return env_vars


def dump_task_definition_settings(config, task_definition, prefix=None, container=0, dump_as_json=True):
    """
    Add the configuration to the task definition appropriately
    overriding any variables

    :param dict config: The configuration to dump
    :param list[dict] task_definition: The task definition
    :param unicode prefix: The prefix of environment variables that
        will be loaded as configuration.  Everything else is ignored
    :param int container: The index of the container to modify
    :param bool dump_as_json: Whether to dump the configuration as
        JSON.
    :return: The updated task_definition as unicode
        It will be indented and the keys will be sorted to
        enforce consistency
    :rtype: unicode
    """
    env_vars = _convert_to_task_definition_environment(config,
                                                       prefix=prefix,
                                                       dump_as_json=dump_as_json)
    existing_env = task_definition[container]['environment']
    existing_env.extend(env_vars)

    existing_keys = set()
    new_env = []
    # Grab the newer ones first
    for env_var in existing_env[::-1]:
        if env_var['name'].upper() in existing_keys:
            continue
        new_env.append(env_var)
        existing_keys.add(env_var['name'].upper())

    # reverse to maintain order
    task_definition[container]['environment'] = new_env[::-1]
    return json.dumps(task_definition, indent=4, sort_keys=True)


def _strip_prefix(key, prefix):
    """
    Strip the prefix from the key.
    Returns None if the key does not
    have the specified prefix

    :param unicode key:
    :param unicode prefix:
    :return: The prefix-free key
    :rtype: unicode
    """
    if prefix and key.startswith('%s_' % prefix):
        return key[len(prefix) + 1:]
    elif not prefix:
        return key
    return None
