from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import json
import unittest

from mock import Mock

from ultra_config.extensions.aws import create_kms_decrypter, encrypt_kms, \
    _strip_prefix, load_task_definition_settings, dump_task_definition_settings, \
    _convert_to_task_definition_environment, create_kms_encrypter


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

    def test_create_kms_encrypter(self):
        resp = create_kms_encrypter(self.client, 'blah')
        self.assertTrue(callable(resp))
        resp(self.value)
        self.assertTrue(self.client.encrypt.called)


class TestLoadTaskDefinitionSettings(unittest.TestCase):
    def test_when_load_as_json__load_json_strings(self):
        td = [{'environment': [{'name': 'blah', 'value': '1'}]}]
        resp = load_task_definition_settings(td)
        self.assertEqual(1, resp['blah'])

    def test_when_not_load_as_json__dont_load_json(self):
        td = [{'environment': [{'name': 'b', 'value': '1'}]}]
        resp = load_task_definition_settings(td, load_as_json=False)
        self.assertEqual('1', resp['b'])

    def test_when_prefix_doesnt_match__skip(self):
        td = [{'environment': [{'name': 'b', 'value': '1'}, {'name': 'PREFIX_some', 'value': 'blah'}]}]
        resp = load_task_definition_settings(td, prefix='PREFIX')
        self.assertDictEqual({'some': 'blah'}, resp)

    def test_ensure_uses_correct_container(self):
        td = [
            {'environment': [{'name': 'a', 'value': 'a'}]},
            {'environment': [{'name': 'b', 'value': 'b'}]}
        ]
        resp = load_task_definition_settings(td, container=1)
        self.assertDictEqual({'b': 'b'}, resp)


class TestConvertToTaskDefinitionEnvironment(unittest.TestCase):
    def test_when_prefix_none__use_raw_key(self):
        config = {'blah': 'blah'}
        resp = _convert_to_task_definition_environment(config)
        self.assertEqual('blah', resp[0]['name'])

    def test_when_prefix_not_none__prepend_prefix(self):
        config = {'blah': 'blah'}
        resp = _convert_to_task_definition_environment(config, prefix='something')
        self.assertEqual('something_blah', resp[0]['name'])

    def test_ensure_format_correct(self):
        config = {'blah': 'b'}
        resp = _convert_to_task_definition_environment(config)
        self.assertEqual('blah', resp[0]['name'])
        self.assertEqual('b', resp[0]['value'])

    def test_when_dump_as_json__all_strings(self):
        config = {'b': {'something': 'another'}}
        resp = _convert_to_task_definition_environment(config)
        self.assertEqual(json.dumps(config['b']), resp[0]['value'])

    def test_when_not_dump_as_json__leave_raw(self):
        config = {'b': {'something': 'another'}}
        resp = _convert_to_task_definition_environment(config, dump_as_json=False)
        self.assertDictEqual(config['b'], resp[0]['value'])


class TestDumpTaskDefinitionSettings(unittest.TestCase):
    def test_ensure_appropriate_container_updated(self):
        task_definition = [
            {
                'environment': [{'name': 'other', 'value': 'something'}]
            },
            {
                'environment': [{'name': 'blah', 'value': 'original'}]
            }
        ]
        resp = dump_task_definition_settings({'blah': 'new'}, task_definition, container=1)
        resp = json.loads(resp)
        self.assertEqual(1, len(resp[1]['environment']))
        self.assertEqual('new', resp[1]['environment'][0]['value'])
        self.assertEqual(1, len(resp[0]['environment']))
        self.assertEqual('something', resp[0]['environment'][0]['value'])

    def test_when_existing_configuration_matches__override_configuration(self):
        td = [{'environment': [{'name': 'something', 'value': 'other'}]}]
        resp = json.loads(dump_task_definition_settings({'something': 'new'}, td))
        self.assertEqual('new', resp[0]['environment'][0]['value'])
        self.assertEqual('something', resp[0]['environment'][0]['name'])

    def test_when_existing_configuration_does_not_match__use_existing(self):
        td = [{'environment': [{'name': 'something', 'value': 'other'}]}]
        resp = json.loads(dump_task_definition_settings({'new': 'new'}, td))
        self.assertEqual(2, len(resp[0]['environment']))
        self.assertEqual('other', resp[0]['environment'][0]['value'])
        self.assertEqual('something', resp[0]['environment'][0]['name'])
        self.assertEqual('new', resp[0]['environment'][1]['value'])
        self.assertEqual('new', resp[0]['environment'][1]['name'])


class TestStripPrefix(unittest.TestCase):
    def test_when_no_prefix__return_original(self):
        resp = _strip_prefix('blah', None)
        self.assertEqual('blah', resp)

    def test_when_prefix_not_match__return_none(self):
        resp = _strip_prefix('blah', 'prefix')
        self.assertIsNone(resp)

    def test_when_prefix_match__return_stipped_key(self):
        resp = _strip_prefix('PREFIX_BLAH', 'PREFIX')
        self.assertEqual('BLAH', resp)
