import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.BaseUnit import BaseUnit
from StringIO import StringIO
from os.path import join, abspath, dirname
from os import curdir
from utils import normalize_html, showdiff

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

class BaseUnitTest( unittest.TestCase ):

    def setUp(self):
        self.file = open(join(_prefix, 'input', 'test1.rst'))
        self.bu = BaseUnit('test', self.file, 'text/restructured')

    def test_defaulthtml(self):
        out = open(join(_prefix, 'output', 'test1_default.html'))
        expected = out.read()
        out.close()
        got = self.bu()
        got = normalize_html(got)
        expected = normalize_html(expected)
        # useful for debugging
        # print showdiff(got, expected)
        self.assertEquals(got, expected)

    def tearDown(self):
        self.file.close()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BaseSchemaTest),
        ))

if __name__ == '__main__':
    unittest.main()
