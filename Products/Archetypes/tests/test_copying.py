################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""
Unittests for a copying/cutting and pasting archetypes objects.

$Id$
"""

import os

import transaction
from Acquisition import aq_base

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.tests.atsitetestcase import portal_owner
from Products.Archetypes.tests.atsitetestcase import portal_name
from Products.Archetypes.tests.atsitetestcase import default_user

from Products.Archetypes.tests.utils import PACKAGE_HOME

class CutPasteCopyPasteTests(ATSiteTestCase):

    def test_copy_and_paste(self):
        ffrom = makeContent(self.folder, portal_type='SimpleFolder', id='cangucu')
        tourist = makeContent(ffrom, portal_type='Fact', id='tourist')
        fto = makeContent(self.folder, portal_type='SimpleFolder', id='london')
        self.failIf('tourist' not in ffrom.contentIds())

        #make sure we have _p_jar
        transaction.savepoint(optimistic=True)
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
        transaction.savepoint(optimistic=True)
        cb = ffrom.manage_cutObjects(ffrom.contentIds())
        fto.manage_pasteObjects(cb)
        self.failIf('tourist' in ffrom.contentIds())
        self.failIf('tourist' not in fto.contentIds())

class PortalCopyTests(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self.setRoles(['Manager',])

        imgpath = os.path.join(PACKAGE_HOME, os.pardir, 'tool.gif')
        self._image = open(imgpath).read()

        portal = self.portal

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
        portal = self.portal
        self.failUnless(portal, 'document')
        doc = portal.document
        self._test_doc(doc)

    def test_clone_portal(self):
        app = self.app
        user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
        newSecurityManager(None, user)
        app.manage_clone(self.portal, 'newportal')
        noSecurityManager()
        transaction.savepoint(optimistic=True)

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
        transaction.savepoint(optimistic=True)

        self.failUnless(hasattr(aq_base(self.app), 'copy_of_%s' % portal_name))
        self.newportal = getattr(self.app, 'copy_of_%s' % portal_name)
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
        transaction.savepoint(optimistic=True)

        self.failUnless(hasattr(aq_base(self.app), portal_name))
        self.newportal = getattr(self.app, portal_name)

        self.failUnless(hasattr(aq_base(self.newportal), 'document'))
        doc = self.newportal.document
        self._test_doc(doc)

    def test_copy_paste_sets_ownership(self):
        # Copy/pasting a File should set new ownership including local roles
        # borrowed from CMFCore tests

        # First, create a new manager user
        uf = self.portal.acl_users
        uf._doAddUser('manager1', 'secret', ['Manager'], [])
        member = uf.getUser(default_user).__of__(uf)
        manager1 = uf.getUser('manager1').__of__(uf)
        member_area = self.portal.Members[default_user]

        # Switch to the manager user context and plant a content item into
        # the member user's member area
        self.login('manager1')
        member_area.invokeFactory('DDocument', id='test_file')

        # Switch to "member" context now and try to copy and paste the
        # content item created by "manager1"
        self.login(default_user)
        cb = member_area.manage_copyObjects(['test_file'])
        member_area.manage_pasteObjects(cb)

        # Now test executable ownership and "owner" local role
        # "member" should have both.
        file_ob = member_area.copy_of_test_file
        self.assertEqual(aq_base(file_ob.getOwner().getId()), aq_base(member).getId())
        self.failUnless('Owner' in
                            file_ob.get_local_roles_for_userid(default_user))

    def test_copy_paste_resets_workflow(self):
        # Copy/pasting a File should reset workflow to the default state

        # This test depends on the default wf, assume CMFDefault if plone
        # isn't present
        wf_tool = self.portal.portal_workflow
        if 'plone_workflow' in wf_tool.objectIds():
            wf_id = 'plone_workflow'
            def_state = 'visible'
        else:
            wf_id = 'default_workflow'
            def_state = 'private'

        wf_tool.setChainForPortalTypes(('DDocument',), (wf_id,))
        self.folder.invokeFactory('DDocument', id='test_file')

        file = self.folder.test_file

        self.assertEqual(wf_tool.getInfoFor(file, 'review_state'), def_state)
        wf_tool.doActionFor(file, 'publish')
        self.assertEqual(wf_tool.getInfoFor(file, 'review_state'),
                                                                 'published')

        cb = self.folder.manage_copyObjects(['test_file'])
        self.folder.manage_pasteObjects(cb)

        file_copy = self.folder.copy_of_test_file
        self.assertEqual(wf_tool.getInfoFor(file_copy, 'review_state'),
                                                                   def_state)

    def test_cut_paste_preserves_workflow(self):
        # Cut/pasting a File should preserve workflow state

        # This test depends on the default wf, assume CMFDefault if plone
        # isn't present
        wf_tool = self.portal.portal_workflow
        if 'plone_workflow' in wf_tool.objectIds():
            wf_id = 'plone_workflow'
            def_state = 'visible'
        else:
            wf_id = 'default_workflow'
            def_state = 'private'

        wf_tool.setChainForPortalTypes(('DDocument',), (wf_id,))
        self.folder.invokeFactory('DDocument', id='test_file')
        self.folder.invokeFactory('Folder', id='sub')

        file = self.folder.test_file

        self.assertEqual(wf_tool.getInfoFor(file, 'review_state'), def_state)
        wf_tool.doActionFor(file, 'publish')
        self.assertEqual(wf_tool.getInfoFor(file, 'review_state'),
                                                                 'published')

        transaction.savepoint(optimistic=True)
        cb = self.folder.manage_cutObjects(['test_file'])
        self.folder.sub.manage_pasteObjects(cb)

        file_copy = self.folder.sub.test_file
        self.assertEqual(wf_tool.getInfoFor(file_copy, 'review_state'),
                                                                 'published')

    def test_copy_handles_talkback_Items(self):
        # We need to ensure that the manage_after* methods are called on
        # subobjects of non-folderish objects
        doc = self.portal.document
        dtool = self.portal.portal_discussion
        cat = self.portal.portal_catalog

        doc.allowDiscussion('1')
        tb = dtool.getDiscussionFor(doc)
        tb.createReply(title='Stupendous', text='silly', Creator='admin')

        # Creating the reply should have cataloged it in manage_afterAdd
        results = cat(Title='Stupendous')
        self.assertEqual(len(results), 1)

        cp = self.portal.manage_copyObjects(ids=['document'])
        self.folder.manage_pasteObjects(cp)
        doc_copy = self.folder.document

        tb = dtool.getDiscussionFor(doc_copy)
        self.failUnless(tb.hasReplies(doc_copy), "Discussion not copied")

        # Copying doc should have cataloged the reply in manage_afterClone
        results = cat(Title='Stupendous')
        self.assertEqual(len(results), 2)

    # not sure where else to put this
    def test_delete_handles_talkback_Items(self):
        doc = self.portal.document
        dtool = self.portal.portal_discussion
        cat = self.portal.portal_catalog

        doc.allowDiscussion('1')
        tb = dtool.getDiscussionFor(doc)
        tb.createReply(title='Stupendous', text='silly', Creator='admin')

        # Creating the reply should have cataloged it in manage_afterAdd
        results = cat(Title='Stupendous')
        self.assertEqual(len(results), 1)

        self.portal.manage_delObjects(ids=['document'])

        # Deleting the doc should have removed the discussions from the
        # catalog
        results = cat(Title='Stupendous')
        self.assertEqual(len(results), 0)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(CutPasteCopyPasteTests))
    suite.addTest(makeSuite(PortalCopyTests))
    return suite
