from __future__ import absolute_import

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


import funconf


class TestWrapsParameters(unittest.TestCase):

    def test_wrapped(self):
        kwargs = dict(a=1)
        @funconf.wraps_parameters(kwargs)
        def main(**k):
            return k
        self.assertTrue(kwargs == main())
        self.assertTrue(kwargs == main(a=5))
        self.assertTrue(kwargs != main(c=5))
        self.assertEqual({'a':5, 'c':5}, main(c=5))
        self.assertTrue(kwargs is not main())

    def test_wrapped_no_params(self):
        @funconf.wraps_parameters({})
        def main(**k):
            return k
        self.assertTrue({} == main())

    def test_keyword_with_var(self):
        @funconf.wraps_parameters({})
        def main(a=3, **k):
            return (a, k)
        a, k = main(a=4)
        self.assertTrue(k == {})
        self.assertTrue(a == 4)
        a, k = main(b=6)
        self.assertTrue(k == {'b':6})
        self.assertTrue(a == 3)
        a, k = main()
        self.assertTrue(k == {})
        self.assertTrue(a == 3)
 
    def test_with_no_var_keywords(self):
        conf = dict(b=4)
        @funconf.wraps_parameters(conf)
        def main(a=4):
            return a
        self.assertTrue(main(b=5) == 4)
        self.assertTrue(dict(b=5) == conf)

    def test_positional_arg(self):
        conf = dict(a=4)
        @funconf.wraps_parameters(conf)
        def main(a, b):
            self.assertEqual(conf, {'a':a})
        main(4, 5)
        main('afs', 'foo')

    def test_positional_keyword_arg(self):
        conf = dict(a=4)
        @funconf.wraps_parameters(conf)
        def main(b, a=2):
            return a
        self.assertEqual(main(-1, 33), 33)
        self.assertEqual(main(-1), 33)
        self.assertEqual(conf, {'a':33})
        self.assertEqual(main(a=5, b=-1), 5)
        self.assertEqual(conf, {'a':5})

    def test_arg_in_kwarg(self):
        conf = dict(blob=4)
        @funconf.wraps_parameters(conf)
        def main(blob=3):
            return blob
        self.assertEqual(main(), 4)
        self.assertEqual(main(blob=2), 2)

    def test_hide_var_keyword(self):
        conf = dict()
        @funconf.wraps_parameters(conf, hide_var_keyword=True)
        def main(a=3, **k):
            pass
        main(1)
        sig = signature(main)
        self.assertTrue('k' not in sig.parameters)

    def test_show_var_keyword(self):
        conf = dict()
        @funconf.wraps_parameters(conf, hide_var_keyword=False)
        def main(b, a=3, *p, **k):
            pass
        main(1)
        sig = signature(main)
        self.assertTrue('k' in sig.parameters)
        k = sig.parameters['k']
        self.assertEqual(k.kind, k.VAR_KEYWORD)

    def test_hide_var_positional(self):
        conf = dict()
        @funconf.wraps_parameters(conf, hide_var_positional=True)
        def main(b, a=3, *p, **k):
            return p
        p = main(1, 2, 3)
        self.assertEqual(p, (3,))
        sig = signature(main)
        self.assertTrue('p' not in sig.parameters)

    def test_show_var_positional(self):
        conf = dict()
        @funconf.wraps_parameters(conf, hide_var_positional=False)
        def main(b, a=3, *p, **k):
            return p 
        p = main(1, 2, 3)
        self.assertEqual(p, (3,))
        sig = signature(main)
        self.assertTrue('p' in sig.parameters)
        k = sig.parameters['p']
        self.assertEqual(k.kind, k.VAR_POSITIONAL)

    def test_wraps_wrapper(self):
        conf_1 = dict(a=5, b=2)
        conf_2 = dict(a=4)
        @funconf.wraps_parameters(conf_1)
        @funconf.wraps_parameters(conf_2)
        def inner(a):
            return a
        self.assertEqual(inner(), 5)
        self.assertEqual(inner(6), 6)
        self.assertEqual(inner(a=3), 3)
        self.assertEqual(inner(1, b=2), 1)
        self.assertEqual(inner(11, b=4), 11)
        self.assertEqual(conf_1, dict(a=11, b=4))
        self.assertEqual(conf_2, dict(a=11))

    def test_default_in_keyword(self):
        conf = dict(a=4)
        @funconf.wraps_parameters(conf)
        def main(**k):
            return k['a']
        self.assertEqual(main(), 4)
        self.assertEqual(main(a=2, b=4), 2)


class TestLazyStringCast(unittest.TestCase):
    
    def test_cast_int(self):
        @funconf.lazy_string_cast(dict(a=1))
        def main(**k):
            return k
        self.assertTrue(dict(a=111) == main(a='111'))
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_bool(self):
        @funconf.lazy_string_cast(dict(a=True))
        def main(**k):
            return k
        self.assertTrue(dict(a=False) == main(a='False'))
        self.assertTrue(dict(a=False) == main(a='f'))
        self.assertTrue(dict(a=False) == main(a='false'))
        self.assertTrue(dict(a=False) == main(a='n'))
        self.assertTrue(dict(a=False) == main(a='no'))
        self.assertTrue(dict(a=True) == main(a='true'))
        self.assertTrue(dict(a=True) == main(a='t'))
        self.assertTrue(dict(a=True) == main(a='y'))
        self.assertTrue(dict(a=True) == main(a='yes'))
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_float(self):
        @funconf.lazy_string_cast(dict(a=4.0))
        def main(**k):
            return k
        self.assertTrue(dict(a=1.11) == main(a='1.11'))
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_other(self):
        @funconf.lazy_string_cast(dict(a=dict(moo='foo')))
        def main(**k):
            return k
        self.assertTrue(main(a='blah')['a'] == 'blah')

    def test_cast_list_paths(self):
        @funconf.lazy_string_cast(dict(a=[]))
        def main(**k):
            return k
        self.assertEqual(main(a='C:\\Windows\\System32 "foobar \\moo"')['a'],
                               ['C:\\Windows\\System32', 'foobar \\moo'])

    def test_cast_list_int(self):
        @funconf.lazy_string_cast(dict(a=[1]))
        def main(**k):
            return k
        self.assertEqual(main(a='111 222')['a'], [111, 222])
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_list_bool(self):
        @funconf.lazy_string_cast(dict(a=[True]))
        def main(**k):
            return k
        self.assertEqual(main(a='False True')['a'], [False, True])
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_list_float(self):
        @funconf.lazy_string_cast(dict(a=[4.0]))
        def main(**k):
            return k
        self.assertEqual(main(a='34.23 232.1')['a'], [34.23, 232.1])
        self.assertRaises(ValueError, main, a='aaa')

    def test_models_as_func_or_method(self):
        @funconf.lazy_string_cast
        def main(debug=True):
            return debug
        self.assertFalse(main(debug='f'))

    def test_positional(self):
        @funconf.lazy_string_cast(dict(debug=True))
        def main(debug):
            return debug
        self.assertEqual(main('f'), False)

    def test_var_pos_and_var_keyword(self):
        @funconf.lazy_string_cast(dict(debug=True, foobar=4, moo=3))
        def main(debug, foobar=6, *a, **k):
            return debug, foobar, k, a
        debug, foobar, k, a = main('f', 34, 65, 'hi', moo='24')
        self.assertEqual(debug, False)
        self.assertEqual(foobar, 34)
        self.assertEqual(a, (65,'hi'))
        self.assertEqual(k, {'moo':24})

    def test_no_model_var_pos_and_var_keyword(self):
        @funconf.lazy_string_cast
        def main(debug, foobar=6, *a, **k):
            return debug, foobar, k, a
        debug, foobar, k, a = main('f', 34, 65, 'hi', moo='24')
        self.assertEqual(debug, 'f')
        self.assertEqual(foobar, 34)
        self.assertEqual(a, (65,'hi'))
        self.assertEqual(k, {'moo':'24'})

    def test_wraps_wrapper(self):
        @funconf.lazy_string_cast(dict(a=2))
        @funconf.lazy_string_cast(dict(b=2))
        def main(a, b):
            return a, b
        r = main('4', '5')
        self.assertEqual(r, (4, 5))

    def test_wrapped_goes_default(self):
        @funconf.lazy_string_cast(dict(b=2), provide_defaults=True)
        def main(a, b):
            return a
        self.assertEqual(main(2), 2)
        self.assertRaises(TypeError, main)
        self.assertRaises(TypeError, main, 2, 2, 2)

    def test_wrapped_no_defaults(self):
        @funconf.lazy_string_cast(dict(b=2), provide_defaults=False)
        def main(a, b):
            return a
        self.assertRaises(TypeError, main, 2)
        self.assertRaises(TypeError, main)
        self.assertRaises(TypeError, main, 2, 2, 2)

    def test_use_funcs_defaults(self):
        @funconf.lazy_string_cast
        def main(a=False):
            return a
        self.assertEqual(main(), False)


