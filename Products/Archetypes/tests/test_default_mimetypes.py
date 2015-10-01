# test initialisation and setup

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.mimetype_utils import getDefaultContentType
from Products.Archetypes.mimetype_utils import setDefaultContentType


class TestDefaultMimeTypes(ATSiteTestCase):

    def test_ATDocumentDefaultType(self):
        # move portal_properties out of the way. it was not here
        # when we used CMFTestCase and now it fools with the
        # default mimetype tests
        _orignal_pp = self.portal['portal_properties']
        self.portal._delObject('portal_properties', suppress_events=True)
        from Products.CMFCore.utils import _tool_interface_registry
        _marker = object()
        ptool = _tool_interface_registry.pop('portal_properties', _marker)

        self.loginAsPortalOwner()
        # we create a new document:
        self.portal.invokeFactory(
            'DDocument', id='testdoc', title='TestDocument')
        obj = self.portal.testdoc
        # its text field should have the site wide default 'text/plain'
        textfield = obj.getField('body')
        self.assertEqual(textfield.getContentType(obj), 'text/html')
        # and so has the teaser field:
        teaserfield = obj.getField('teaser')
        self.assertEqual(teaserfield.getContentType(obj), 'text/html')

        # then we try to change the sitewide default:
        setDefaultContentType(self.portal, "text/x-web-markdown")
        # while this raises no error it won't change the default, as we have
        # no properties tool nor properties sheet
        self.assertEqual(getDefaultContentType(
            self.portal), 'text/x-web-markdown')
        self.portal['portal_properties'] = _orignal_pp
        if ptool is not _marker:
            _tool_interface_registry['portal_properties'] = ptool
