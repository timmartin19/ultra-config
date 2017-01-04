from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import warnings

from ultra_config import UltraConfig
from ultra_config.secrets import decrypt


class TestDecrypt(unittest.TestCase):
    def test_ensure_warning_raised_when_secrets_key_empty(self):
        config = UltraConfig([])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            decrypt(config, lambda value: 'blah')
            self.assertEqual(len(w), 1)

    def test__when_config_key_set__no_warning(self):
        config = UltraConfig([])
        config['SUPER_SECRET'] = 'asv'
        config['SECRETS'] = ['SUPER_SECRET']
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            decrypt(config, lambda value: 'blah')
            self.assertEqual(len(w), 0)
        self.assertEqual(config['SUPER_SECRET'], 'blah')

    def test__when_config_key_none__no_warning(self):
        config = UltraConfig([])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            decrypt(config, lambda value: 'blah', secrets_config_key=None)
            self.assertEqual(len(w), 0)

    def test__when_secrets_config_key_set__use_secrets_config_key(self):
        config = UltraConfig([])
        config['SUPER_SECRET'] = 'asv'
        config['MY_SECRETS'] = ['SUPER_SECRET']
        config['SECRETS'] = ['OTHER_SECRET']
        config['OTHER_SECRET'] = 'not-secret'
        decrypt(config, lambda value: 'blah', secrets_config_key='MY_SECRETS')
        self.assertEqual(config['SUPER_SECRET'], 'blah')
        self.assertEqual(config['OTHER_SECRET'], 'not-secret')

    def test__when_secrets_list_set__use_secrets_list(self):
        config = UltraConfig([])
        config['SUPER_SECRET'] = 'asv'
        decrypt(config, lambda value: 'blah', secrets_config_key=None, secrets_list=['SUPER_SECRET'])
        self.assertEqual(config['SUPER_SECRET'], 'blah')


