import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

import glob
import os

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME
from Products.Archetypes.tests.utils import normalize_html
from Products.Archetypes.tests.utils import gen_class
from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy


class BaseUnitTest( ATSiteTestCase ):

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

input_files = glob.glob(os.path.join(PACKAGE_HOME, "input", "rest*.rst"))
for f in input_files:
    fname = os.path.split(f)[1]
    outname = os.path.join(PACKAGE_HOME, "output", '%s.out' % fname.split('.')[0])

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
