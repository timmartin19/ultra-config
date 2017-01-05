from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import unittest

from ultra_config import simple_config, load_json_file_settings, \
    load_configparser_settings, load_python_object_settings, load_dict_settings, \
    UltraConfig
from ultra_config_tests.unit_tests import default_config


class TestSimpleConfig(unittest.TestCase):
    def test_default_config(self):
        config = simple_config(default_settings=default_config)
        self.assertNotIn('__IGNORE__', config)
        self.assertNotIn('IGNORE', config)
        self.assertEqual('x', config['SOMETHING'])
        self.assertEqual('z', config['ANOTHER'])

    def test_override_order(self):
        settings_dir = os.path.join(os.path.dirname(__file__), '..', 'settings')
        json_filename = os.path.join(settings_dir, 'json_settings.json')
        os.environ['PREFIX_ENV_VAR_OVERRIDE'] = '2'
        os.environ['PREFIX_OVERRIDE'] = '1'
        config = simple_config(default_settings=default_config,
                               json_file=json_filename,
                               env_var_prefix='PREFIX',
                               overrides=dict(OVERRIDE=2))
        self.assertEqual(2, config['JSON_OVERRIDE'])
        self.assertEqual(2, config['ENV_VAR_OVERRIDE'])
        self.assertEqual(2, config['OVERRIDE'])


class TestLoadJSONFileSettings(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(__file__), '..', 'settings', 'json_settings.json')

    def test_simple(self):
        config = load_json_file_settings(self.filename)
        self.assertEqual(1, config['JSON_1'])
        self.assertEqual(2, config['json_2'])


class TestLoadConfigParserSettings(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(__file__), '..', 'settings', 'config_parser.ini')

    def test_simple(self):
        config = load_configparser_settings(self.filename)
        self.assertIn('ini', config)
        self.assertIn('ini2', config)
        self.assertEqual('1', config['ini']['x'])
        self.assertEqual('2', config['ini']['y'])
        self.assertEqual('3', config['ini2']['z'])


class TestLoadPythonObjects(unittest.TestCase):
    def test_simple(self):
        class SomeObj(object):
            x = 1
            y = 2

        config = load_python_object_settings(SomeObj)
        self.assertEqual(1, config['x'])
        self.assertEqual(2, config['y'])

    def test_dict_simple(self):
        original = dict(x=1, y=2)
        config = load_dict_settings(original)
        self.assertEqual(1, config['x'])
        self.assertEqual(2, config['y'])
        self.assertIsNot(original, config)


class TestUltraConfig(unittest.TestCase):
    def setUp(self):
        self.encrypter = lambda value: 'blah'

    def test_load(self):
        config = UltraConfig([[lambda: dict(x=1, y=2)], [lambda: dict(x=3)]])
        config.load()
        self.assertEqual(config['x'], 3)
        self.assertEqual(config['y'], 2)

    def test_required_items__when_missing__raises_ValueError(self):
        config = UltraConfig([], required=['required'])
        self.assertRaises(ValueError, config.validate)

    def test_required_items__when_found(self):
        config = UltraConfig([], required=['required'])
        config['REQUIRED'] = True
        resp = config.validate()
        self.assertIsNone(resp)

    def test_encrypt__when_already_encrypted__raise_value_error(self):
        config = UltraConfig([])
        config.decrypted = False
        self.assertRaises(ValueError, config.encrypt)

    def test_encrypt__when_not_encrypted__encrypt_secrets(self):
        config = UltraConfig([], encrypter=self.encrypter)
        config['blah'] = 'something'
        config['SECRETS'] = ['blah']
        config.decrypted = True
        config.encrypt()
        self.assertEqual('blah', config['blah'])

    def test_decrypt__when_already_decrypted__raise_value_error(self):
        config = UltraConfig([])
        config.decrypted = True
        self.assertRaises(ValueError, config.decrypt)

    def test_decrypt__when_not_decrypted__decrypt_secrets(self):
        config = UltraConfig([], decrypter=self.encrypter)
        config['blah'] = 'something'
        config['SECRETS'] = ['blah']
        config.decrypted = False
        config.decrypt()
        self.assertEqual('blah', config['blah'])

    def test_set_encrypted__when_encrypted__encrypt_and_set(self):
        config = UltraConfig([], encrypter=self.encrypter)
        config.set_encrypted('blah', 'something')
        self.assertEqual('blah', config['blah'])

    def test_set_encrypted__when_not_encrypted__set_raw_value(self):
        config = UltraConfig([], encrypter=self.encrypter)
        config.decrypted = True
        config.set_encrypted('blah', 'something')
        self.assertEqual('something', config['blah'])

    def test_set_encrypted__ensure_secrets_config_key_extended(self):
        config = UltraConfig([], encrypter=self.encrypter)
        config.set_encrypted('blah', 'blah')
        self.assertListEqual(['blah'], config[config.secrets_config_key])

    def test_set_encrypted__when_key_already_in_secrets__no_duplicates(self):
        config = UltraConfig([], encrypter=self.encrypter)
        config[config.secrets_config_key] = ['blah']
        config.set_encrypted('blah', 'blah')
        self.assertListEqual(['blah'], config[config.secrets_config_key])

    def test_get_encrypted__when_encrypted__decrypt_and_return(self):
        config = UltraConfig([], decrypter=self.encrypter)
        config['blah'] = 'something'
        resp = config.get_encrypted('blah')
        self.assertEqual('blah', resp)

    def test_get_encrypted__when_not_encrypted__return(self):
        config = UltraConfig([], decrypter=self.encrypter)
        config.decrypted = True
        config['blah'] = 'something'
        resp = config.get_encrypted('blah')
        self.assertEqual('something', resp)
