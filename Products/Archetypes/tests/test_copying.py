"""
Unittests for a copying/cutting and pasting archetypes objects.

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

import types
from Acquisition import aq_base

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.tests.atsitetestcase import portal_owner
from Products.Archetypes.tests.atsitetestcase import portal_name
from Products.Archetypes.tests.utils import PACKAGE_HOME

class CutPasteCopyPasteTests(ATSiteTestCase):

    def test_copy_and_paste(self):
        ffrom = makeContent(self.folder, portal_type='SimpleFolder', id='cangucu')
        tourist = makeContent(ffrom, portal_type='Fact', id='tourist')
        fto = makeContent(self.folder, portal_type='SimpleFolder', id='london')
        self.failIf('tourist' not in ffrom.contentIds())

        #make sure we have _p_jar
        get_transaction().commit(1)
        cb = ffrom.manage_copyObjects(ffrom.contentIds())
        fto.manage_pasteObjects(cb)
        self.failIf('tourist' not in ffrom.contentIds())
        self.failIf('tourist' not in fto.contentIds())

    def test_cut_and_paste(self):
        ffrom = makeContent(self.folder, portal_type='SimpleFolder', id='cangucu')
        tourist = makeContent(ffrom, portal_type='Fact', id='tourist')
        fto = makeContent(self.folder, portal_type='SimpleFolder', id='london')
        self.failIf('tourist' not in ffrom.contentIds())

        #make sure we have _p_jar
        get_transaction().commit(1)
        cb = ffrom.manage_cutObjects(ffrom.contentIds())
        fto.manage_pasteObjects(cb)
        self.failIf('tourist' in ffrom.contentIds())
        self.failIf('tourist' not in fto.contentIds())

from Testing.ZopeTestCase.ZopeTestCase import user_name

class PortalCopyTests(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self.setRoles(['Manager',])

        imgpath = os.path.join(PACKAGE_HOME, os.pardir, 'tool.gif')
        self._image = open(imgpath).read()

        portal = self.getPortal()

        portal.invokeFactory('DDocument', id='document')
        doc = portal.document
        doc.setBody('testdata', mimetype='text/x-rst')
        doc.setImage(self._image, mimetype='image/gif')

    def _test_doc(self, doc):
        bodyfield = doc.getField('body')
        imagefield = doc.getField('image')

        self.failUnlessEqual(doc.getContentType(), 'text/x-rst')

        self.failUnlessEqual(doc.getRawBody(), 'testdata')
        self.failUnless(doc.getImage().data, self._image)

        self.failUnless(bodyfield.getContentType(doc), 'text/x-rst')

    def test_created_doc(self):
        portal = self.getPortal()
        self.failUnless(portal, 'document')
        doc = portal.document
        self._test_doc(doc)

    def test_clone_portal(self):
        app = self.app
        user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
        newSecurityManager(None, user)
        app.manage_clone(self.getPortal(), 'newportal')
        noSecurityManager()
        get_transaction().commit(1)

        self.failUnless(hasattr(aq_base(app), 'newportal'))
        self.newportal = app.newportal
        # check if we really have new portal!
        self.failIf(aq_base(self.newportal) is aq_base(self.portal))
        self.failIfEqual(aq_base(self.newportal), aq_base(self.portal))

        self.failUnless(hasattr(aq_base(self.newportal), 'document'))
        doc = self.newportal.document
        self._test_doc(doc)

    def test_copy_paste_portal(self):
        app = self.app
        user = app.acl_users.getUserById('portal_owner').__of__(app.acl_users)
        newSecurityManager(None, user)
        cp = app.manage_copyObjects(ids=[portal_name])
        app.manage_pasteObjects(cb_copy_data=cp)

        noSecurityManager()
        get_transaction().commit(1)

        self.failUnless(hasattr(aq_base(self.app), 'copy_of_%s' % portal_name))
        self.newportal = self.app.copy_of_cmf
        # check if we really have new portal!
        self.failIf(aq_base(self.newportal) is aq_base(self.portal))
        self.failIfEqual(aq_base(self.newportal), aq_base(self.portal))

        self.failUnless(hasattr(aq_base(self.newportal), 'document'))
        doc = self.newportal.document
        self._test_doc(doc)

    def test_cut_paste_portal(self):
        app = self.app
        user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
        newSecurityManager(None, user)
        cp = app.manage_cutObjects(ids=[portal_name])
        app.manage_pasteObjects(cb_copy_data=cp)

        noSecurityManager()
        get_transaction().commit(1)

        self.failUnless(hasattr(aq_base(self.app), portal_name))
        self.newportal = self.app.cmf

        self.failUnless(hasattr(aq_base(self.newportal), 'document'))
        doc = self.newportal.document
        self._test_doc(doc)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(CutPasteCopyPasteTests))
    suite.addTest(makeSuite(PortalCopyTests))
    return suite

if __name__ == '__main__':
    framework()
