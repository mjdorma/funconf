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


class TestConfig(unittest.TestCase):
    pass



class TestConfigSection(unittest.TestCase):
    pass
