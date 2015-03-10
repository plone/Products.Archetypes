from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase


class FactoryTest(ATSiteTestCase):

    def testSimplePortalType(self):
        self.folder.invokeFactory(id="dummy", type_name="SimpleType")
        self.assertEqual(self.folder.dummy.getPtype(), "Simple Type")

    def XXXtestCopiedFTIPortalType(self):
        # A known bug where `default_method` doesn't have the correct
        # portal type available.  For a discussion, see
        # https://dev.plone.org/plone/ticket/6734
        self.folder.invokeFactory(id="dummy", type_name="MySimpleType")
        self.assertEqual(self.folder.dummy.getPtype(), "My Simple Type")
