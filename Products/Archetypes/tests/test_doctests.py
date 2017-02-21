import unittest
import doctest
from plone.testing import layered

from .attestcase import AT_FUNCTIONAL_TESTING

# a list of dotted paths to modules which contains doc tests
DOCTEST_MODULES = (
    'Products.Archetypes.utils',
    'Products.Archetypes.Schema',
    'Products.Archetypes.ArchetypeTool',
    'Products.Archetypes.AllowedTypesByIface',
    'Products.Archetypes.Field',
    'Products.Archetypes.Marshall',
    'Products.Archetypes.fieldproperty',
    'Products.Archetypes.browser.widgets',
)

DOCTEST_FILES = (
    'events.txt',
    'translate.txt',
    'traversal_4981.txt',
    'folder_marshall.txt',
    'webdav_operations.txt',
    'traversal.txt',
)

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    suite = unittest.TestSuite()
    for testmodule in DOCTEST_MODULES:
        suite.addTest(layered(
            doctest.DocTestSuite(testmodule,
                                 optionflags=OPTIONFLAGS),
            layer=AT_FUNCTIONAL_TESTING))
    for testfile in DOCTEST_FILES:
        suite.addTest(layered(
            doctest.DocFileSuite(testfile,
                                 optionflags=OPTIONFLAGS,
                                 package="Products.Archetypes.tests",),
            layer=AT_FUNCTIONAL_TESTING))
    return suite
