#
# Skeleton Archetypes test
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *


class TestSomething(ArchetypesTestCase):

    def afterSetUp(self):
        pass

    def testSomething(self):
        # Test something
        self.assertEqual(1+1, 2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSomething))
    return suite

if __name__ == '__main__':
    framework()
