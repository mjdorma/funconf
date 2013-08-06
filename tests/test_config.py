from __future__ import absolute_import
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from inspect import signature
except ImportError:
    from funcsigs import signature
from io import StringIO
from mock import patch


import funconf


TEST_CONFIG = """
#
# Aaa
#
aaa:
  float: 4.4
  int: 4
  list_int:
  - 1
  - 2
  list_str:
  - aaa
  - bbb


#
# Bbb
#
bbb:
  float: 8.4
  int: 7
  list_int:
  - 3
  - 4
  list_str:
  - bbb
  - ccc

""".strip()
if sys.version_info[0] == 2:
    TEST_CONFIG = unicode(TEST_CONFIG)


class TestConfig(unittest.TestCase):

    @patch('__builtin__.open') 
    def test_print_config(self, mock_open):
        mock_open.return_value = StringIO(TEST_CONFIG)
        config = funconf.Config('mocked.conf')
        self.assertEqual(str(config).strip(), TEST_CONFIG)

    @patch('__builtin__.open') 
    def test_accessing_attributes(self, mock_open):
        mock_open.return_value = StringIO(TEST_CONFIG)
        config = funconf.Config('mocked.conf')
        self.assertEqual(config.aaa.int, 4)
        config.aaa.int = 5
        self.assertEqual(config.aaa.int, 5)
        self.assertRaises(funconf.ConfigAttributeError, getattr, config, 'nope')
        self.assertRaises(funconf.ConfigAttributeError, getattr, config.aaa,
                'nope')
        


