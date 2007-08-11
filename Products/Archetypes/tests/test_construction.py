import unittest
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase


class FactoryTest(ATSiteTestCase):
    def testSimplePortalType(self):
        self.folder.invokeFactory(id="dummy", type_name="SimpleType")
        self.assertEqual(self.folder.dummy.getPtype(), "Simple Type")

    def testCopiedFTIPortalType(self):
        self.folder.invokeFactory(id="dummy", type_name="MySimpleType")
        self.assertEqual(self.folder.dummy.getPtype(), "My Simple Type")

def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FactoryTest))
    return suite
