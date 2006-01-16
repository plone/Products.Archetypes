import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME, USE_NEW_BASEUNIT
from Products.Archetypes.BaseUnit import BaseUnit
from StringIO import StringIO
from os.path import join, abspath, dirname, split
from os import curdir
import glob
from utils import normalize_html, showdiff

from test_classgen import Dummy, gen_dummy

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

class BaseUnitTest( unittest.TestCase ):

    def testSame(self):
        gen_dummy()
        dummy = Dummy(oid='dummy', init_transforms=1)
        input = open(self.input)
        bu = BaseUnit(name='test', file=input, mimetype='text/restructured',
                      instance=dummy)
        input.close()
        if USE_NEW_BASEUNIT:
            got = normalize_html(bu.transform(dummy, 'text/html'))
        else:
            got = normalize_html(bu())
        output = open(self.output)
        expected = normalize_html(output.read())
        output.close()

        self.assertEquals(got, expected)

tests = []

input_files = glob.glob(join(_prefix, "input", "rest*.rst"))
for f in input_files:
    fname = split(f)[1]
    outname = join(_prefix, "output", '%s.out' % fname.split('.')[0])

    class BaseUnitTestSubclass(BaseUnitTest):
        input = f
        output = outname

    tests.append(BaseUnitTestSubclass)

def test_suite():
    return unittest.TestSuite([unittest.makeSuite(test) for test in tests])

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
