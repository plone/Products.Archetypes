from Testing.ZopeTestCase import FunctionalDocFileSuite as FileSuite

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

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase
from Products.Archetypes.tests.doctestcase import ZopeDocTestSuite

def test_suite():
    suite = ZopeDocTestSuite(test_class=ATSiteTestCase,
                             extraglobs={},
                             *DOCTEST_MODULES
                             )
    for testfile in DOCTEST_FILES:
        suite.addTest(FileSuite(testfile,
                                package="Products.Archetypes.tests",
                                test_class=ATFunctionalSiteTestCase)
                     )
    return suite
