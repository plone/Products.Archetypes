import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
from Testing import ZopeTestCase
from common import *
from utils import *

from Products.CMFCore.utils import getToolByName
package = 'Products.Archetypes.tests'

class FunctionalTest(ZopeTestCase.Functional,
                     ArcheSiteTestCase):
    """Functional Tests for Archetypes"""


def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = ['traversal.txt']
    for f in files:
        suite.addTest(FileSuite(f, test_class=FunctionalTest, package=package))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
