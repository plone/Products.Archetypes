# test initialisation and setup

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from unittest import TestSuite, makeSuite

from Products.Archetypes.mimetype_utils import getDefaultContentType
from Products.Archetypes.mimetype_utils import setDefaultContentType


class TestDefaultMimeTypes(ATSiteTestCase):

    def test_ATDocumentDefaultType(self):
        self.loginAsPortalOwner()
        # we create a new document:
        self.portal.invokeFactory('DDocument', id='testdoc', title='TestDocument')
        obj = self.portal.testdoc
        # its text field should have the site wide default 'text/plain'
        textfield = obj.getField('body')
        self.assertEqual(textfield.getContentType(obj), 'text/plain')
        # and so has the teaser field:
        teaserfield = obj.getField('teaser')
        self.assertEqual(teaserfield.getContentType(obj), 'text/plain')

        # then we try to change the sitewide default:
        setDefaultContentType(self.portal, "text/x-web-markdown")
        # while this raises no error it won't change the default, as we have
        # no properties tool nor properties sheet
        self.assertEqual(getDefaultContentType(self.portal), 'text/plain')

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestDefaultMimeTypes))
    return suite

