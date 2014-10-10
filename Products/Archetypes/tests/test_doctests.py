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

DOCTEST_FILES = ('events.txt', )


def test_suite():
    suite = unittest.TestSuite()
    for testmodule in DOCTEST_MODULES:
        suite.addTest(layered(
            doctest.DocTestSuite(testmodule),
            layer=AT_FUNCTIONAL_TESTING))
    for testfile in DOCTEST_FILES:
        suite.addTest(layered(
            doctest.DocFileSuite(testfile,
                                 package="Products.Archetypes.tests",),
            layer=AT_FUNCTIONAL_TESTING))
    return suite
