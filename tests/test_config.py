from __future__ import absolute_import
try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from inspect import signature
except ImportError:
    from funcsigs import signature
import sys
try:
    u = unicode
except NameError:
    u = lambda x: x

if sys.version_info[0] == 2:
    builtins_mod = "__builtin__"
else:
    builtins_mod = "builtins"
     
from io import StringIO
from mock import patch
import yaml

import funconf


TEST_CONFIG = u("""
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

""".strip())


class TestConfig(unittest.TestCase):

    @patch('%s.open' % builtins_mod) 
    def test_print_config(self, mock_open):
        mock_open.return_value = StringIO(TEST_CONFIG)
        config = funconf.Config('mocked.conf')
        as_str = str(config)
        self.assertEqual(len(config), 8)
        self.assertEqual(len(config.bbb), 4)

    @patch('%s.open' % builtins_mod) 
    def test_accessing_strict_attributes(self, mock_open):
        mock_open.return_value = StringIO(TEST_CONFIG)
        config = funconf.Config('mocked.conf')
        self.assertEqual(config.aaa.int, 4)
        config.aaa.int = 5
        self.assertEqual(config.aaa.int, 5)
        self.assertRaises(funconf.ConfigAttributeError, getattr, config.aaa,
                'nope')
        
    @patch('%s.open' % builtins_mod) 
    def test_empty_config(self, mock_open):
        mock_open.return_value = StringIO(u(""))
        config = funconf.Config('mocked.conf')

    @patch('%s.open' % builtins_mod)
    def test_empty_section(self, mock_open):
        mock_open.return_value = StringIO(u("empty: 1"))
        config = funconf.Config('mocked.conf')

    @patch('%s.open' % builtins_mod)
    def test_broken_yaml(self, mock_open):
        mock_open.return_value = StringIO(u("`empty:a df asd Z X324!~ 1"))
        self.assertRaises(yaml.scanner.ScannerError, 
                funconf.Config, 'mocked.conf')

    def test_strict_config(self):
        config = funconf.Config(strict=True)
        self.assertRaises(funconf.ConfigAttributeError, getattr, config, 'nope')

    def test_not_strict_config(self):
        config = funconf.Config()
        self.assertTrue(dict(config.foo) == {})

    def test_file_doesnt_exist(self):
        funconf.Config(['blaoo.con'])

    def test_load_string(self):
        config = funconf.Config()
        config.load(TEST_CONFIG)

    def test_setting(self):
        config = funconf.Config()
        config.set('foo', 'bar', [34, 2, 5])
        config.set('foo', 'moo', "shoe")
        config.set('foo', 'bar', 24.22323)
        config.set('bread', 'milk', True)
        config.set('bread', 'butter', False)
        self.assertTrue(config.bread.milk)

    def test_setting_attributes(self):
        config = funconf.Config()
        self.assertRaises(Exception, setattr, config, 'blah', 4)
        config.set('foo', 'bar', False)
        self.assertRaises(Exception, setattr, config.foo, 'blah', 4)
        config.foo.bar = True
        self.assertTrue(config.foo.bar)

    def test_delattr(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        self.assertRaises(NotImplementedError, config.__delitem__, 'foo')
        self.assertRaises(NotImplementedError, config.foo.__delitem__, 'bar')

    def test_reserved_words(self):
        config = funconf.Config()
        self.assertRaises(ValueError, config.set, 'set', 'foo', True)
        config.set('foo', 'bar', False)
        self.assertRaises(ValueError, config.set, 'foo', 'items', True)
 
    def test_dirty(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        self.assertTrue(config.foo.dirty)
        self.assertFalse(config.foo.dirty)

    def test_config_setitem_getitem(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        self.assertFalse(config['foo_bar'])
        self.assertFalse(config.foo['bar'])
        self.assertRaises(ValueError, config.__setitem__, 'blah', 4)
        self.assertRaises(KeyError, config.__getitem__, 'blah')

    def test_dir(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        self.assertTrue('foo' in dir(config))
        self.assertTrue('bar' in dir(config.foo))

    def test_config_decorate(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        @config
        def func(**k):
            self.assertFalse(k['foo_bar'])
        func()
        func(foo_bar='f')

    def test_config_section_decorate(self):
        config = funconf.Config()
        config.set('foo', 'bar', False)
        @config.foo
        def func(**k):
            self.assertFalse(k['bar'])
        func()

    def test_not_lazy_flag(self):
        config = funconf.Config()
        @config(lazy=False)
        def func(foo=True):
            return foo 
        self.assertEqual(func(foo="y"), "y")
        @config.bar(lazy=False)
        def func(foo=True):
            return foo 
        self.assertEqual(func(foo="y"), "y")

    def test_is_lazy_flag(self):
        config = funconf.Config()
        @config(lazy=True)
        def func(foo=True):
            return foo 
        self.assertEqual(func(foo="y"), True)
        @config.bar(lazy=True)
        def func(foo=True):
            return foo 
        self.assertEqual(func(foo="y"), True)

    def test_wrapped_goes_default(self):
        config = funconf.Config()
        config.set('foo', 'car', 3)
        @config.foo
        def main(bar, car):
            return bar
        self.assertEqual(main(2), 2)

    def test_lazy_cast_not_in_config(self):
        config = funconf.Config()
        @config
        def main(foo=True):
            return foo
        self.assertTrue(main('t') is True)

    def test_positional_or_keyword_with_no_option(self):
        #relates to issue #1 
        config = funconf.Config()
        config.set('foo', 'a', 3)
        @config.foo
        def bread(**k):
            return k
        self.assertRaises(TypeError, bread, 1)

    def test_positional_or_keyword_with_var_args(self):
        #relates to issue #1 
        config = funconf.Config()
        config.set('foo', 'a', 3)
        @config.foo
        def bread(*b, **k):
            return b
        a = bread(4)
        self.assertEqual(a, (4, ))
        @config.foo
        def bread(a, **k):
            return a
        a = bread(4)
        @config.foo
        def bread(b, **k):
            return b
        a = bread(4)
        self.assertEqual(a, 4)
       


