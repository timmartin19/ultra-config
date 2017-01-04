from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import unittest

from mock import Mock

from ultra_config.extensions.aws import create_kms_decrypter, encrypt_kms


class TestKMSDecryption(unittest.TestCase):
    def setUp(self):
        self.value = b'blah'
        self.client = Mock(decrypt=Mock(return_value={'Plaintext': self.value}))

    def test_decrypt_when_utf8(self):
        decrypter = create_kms_decrypter(self.client)
        decrypter(base64.b64encode(self.value).decode('utf-8'))
        self.assertEqual(self.client.decrypt.call_args[1]['CiphertextBlob'], self.value)

    def test_decrypt_when_not_utf8(self):
        decrypter = create_kms_decrypter(self.client)
        decrypter(base64.b64encode(self.value))
        self.assertEqual(self.client.decrypt.call_args[1]['CiphertextBlob'], self.value)

    def test_decrypt_when_not_decode(self):
        decrypter = create_kms_decrypter(self.client, decode=False)
        resp = decrypter(base64.b64encode(self.value).decode('utf-8'))
        self.assertEqual(self.value, resp)

    def test_decrypt_when_decode(self):
        decrypter = create_kms_decrypter(self.client, decode=True)
        resp = decrypter(base64.b64encode(self.value).decode('utf-8'))
        self.assertEqual(self.value.decode('utf-8'), resp)


class TestEncryptKMS(unittest.TestCase):
    def setUp(self):
        self.value = 'blah'
        self.client = Mock(encrypt=Mock(return_value={'CiphertextBlob': self.value.encode('utf-8')}))

    def test_ensure_properly_encoded(self):
        resp = encrypt_kms(self.client, 'blah', self.value)
        resp = base64.b64decode(resp.encode('utf-8')).decode('utf-8')
        self.assertEqual(self.value, resp)

    def test__when_unicode(self):
        encrypt_kms(self.client, 'blah', self.value)
        self.assertEqual(self.value.encode('utf-8'), self.client.encrypt.call_args[1]['Plaintext'])

    def test__when_not_unicode(self):
        encrypt_kms(self.client, 'blah', self.value.encode('utf-8'))
        self.assertEqual(self.value.encode('utf-8'), self.client.encrypt.call_args[1]['Plaintext'])
