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


class TestWrapsKwargs(unittest.TestCase):

    def test_wrapped(self):
        kwargs = dict(a=1, b=2)
        @funconf.wraps_var_kwargs(kwargs)
        def main(**k):
            return k
        self.assertTrue(kwargs == main())
        self.assertTrue(kwargs == main(a=5))
        self.assertRaises(TypeError, main, c=5)
        self.assertTrue(kwargs is not main())

    def test_wrapped_no_params(self):
        @funconf.wraps_var_kwargs({})
        def main(**k):
            return k
        self.assertTrue({} == main())

    def test_non_var_keyword(self):
        def var_arg(*a):
            pass
        def fixed_arg(a, b):
            pass
        def fixed_kwargs(k=3,b=4):
            pass
        decorator = funconf.wraps_var_kwargs({})
        self.assertRaises(ValueError,  decorator, var_arg)
        self.assertRaises(ValueError,  decorator, fixed_arg)
        self.assertRaises(ValueError,  decorator, fixed_kwargs)


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

    def test_cast_list_int(self):
        @funconf.lazy_string_cast(dict(a=[1]))
        def main(**k):
            return k
        self.assertTrue(main(a='111 222')['a'] == [111, 222])
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_list_bool(self):
        @funconf.lazy_string_cast(dict(a=[True]))
        def main(**k):
            return k
        self.assertTrue(main(a='False True')['a'] == [False, True])
        self.assertRaises(ValueError, main, a='aaa')

    def test_cast_list_float(self):
        @funconf.lazy_string_cast(dict(a=[4.0]))
        def main(**k):
            return k
        self.assertTrue(main(a='34.23 232.1')['a'] == [34.23, 232.1])
        self.assertRaises(ValueError, main, a='aaa')



