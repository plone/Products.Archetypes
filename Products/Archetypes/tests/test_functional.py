import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase

from Products.CMFCore.utils import getToolByName

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    #basepath = os.path.dirname(os.path.abspath(__file__))
    files = ['traversal.txt']
    for file in files:
        suite.addTest(FileSuite(file, package="Products.Archetypes.tests",
                                test_class=ATFunctionalSiteTestCase)
                     )
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
