import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.Archetypes.tests.common import *

import glob
from os import curdir
from os.path import join, abspath, dirname, split

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.BaseUnit import BaseUnit

from test_classgen import Dummy, gen_dummy


class BaseUnitTest( ArchetypesTestCase ):

    def testSame(self):
        gen_dummy()
        # The BaseUnit expects 'instance' to be
        # acquisition wrapped, or else it does return
        # the untransformed text -- this was introduced
        # for compatibility with APE.
        parent = Dummy(oid='parent')
        dummy = Dummy(oid='dummy', init_transforms=1).__of__(parent)
        input = open(self.input)
        bu = BaseUnit(name='test', file=input,
                      mimetype='text/restructured',
                      instance=dummy)
        input.close()
        got = normalize_html(bu.transform(dummy, 'text/html'))
        output = open(self.output)
        expected = normalize_html(output.read())
        output.close()

        self.assertEquals(got, expected)

tests = []

input_files = glob.glob(join(PACKAGE_HOME, "input", "rest*.rst"))
for f in input_files:
    fname = split(f)[1]
    outname = join(PACKAGE_HOME, "output", '%s.out' % fname.split('.')[0])

    class BaseUnitTestSubclass(BaseUnitTest):
        input = f
        output = outname

    tests.append(BaseUnitTestSubclass)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()
