from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from ultra_config.case_insensitive_dict import CaseInsensitiveDict


class TestCaseInsensitiveDict(unittest.TestCase):
    def test_pop(self):
        d = CaseInsensitiveDict()
        d['Item'] = 1
        self.assertEqual(1, d.pop('ITEM'))

    def test_same_case(self):
        d = CaseInsensitiveDict(x=1)
        self.assertEqual(1, d['x'])

    def test_different_case(self):
        d = CaseInsensitiveDict(x=1)
        self.assertEqual(1, d['X'])
