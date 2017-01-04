from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
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
    resp = client.encrypt(KeyId=key_id, Plaintext=value)
    encrypted = resp['CiphertextBlob']
    encrypted = base64.b64encode(encrypted)
    return encrypted.decode('utf-8')
