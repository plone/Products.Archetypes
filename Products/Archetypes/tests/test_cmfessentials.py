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

from Testing.ZopeTestCase import user_password
from Products.Five.testbrowser import Browser

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase
from Products.Archetypes.tests.utils import makeContent


from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore import permissions


class TestPermissions(ATSiteTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        # install AT within portal
        self.login()
        self.demo_instances = []
        for t in self.demo_types:
            # XXX: Fails with "Unauthorized" exception from
            #      CMFDefault/DiscussionTool.py:84, in overrideDiscussionFor
            #
            #      Note that BaseObject.initializeArchetype has a bare except
            #      that prints out the error instead of letting it through, so
            #      that there is no exception when running the test.
            inst = makeContent(self.folder, portal_type=t, id=t)
            self.demo_instances.append(inst)

    def testPermissions(self):
        for content in self.demo_instances:
            # XXX: Strangely enough we have correct permissions here, but not so
            #      in initializeArchetype
            self.failUnless(checkPerm(permissions.View, content))
            self.failUnless(checkPerm(permissions.AccessContentsInformation, content))
            self.failUnless(checkPerm(permissions.ModifyPortalContent, content))

    def testRendering(self):
        # Attempt to call each object and make sure it presents a rendered
        # html view
        for content in self.demo_instances:
            self.failUnless(isinstance(content(), basestring))
            self.failUnless(content().strip().startswith('<!DOCTYPE'))


class TestFTICopy(ATFunctionalSiteTestCase):
    """Test for http://dev.plone.org/plone/ticket/6734: Cannot filter
    Addable Types with folderish FTI in portal_types.
    """
    
    def test6734(self):
        self.loginAsPortalOwner()

        # We start off by copying the existing SimpleFolder type to
        # our own type 'MySimpleFolder'.  For this type, we set the
        # SimpleFolder type to be the sole allowed content type.
        types = self.portal.portal_types
        types.manage_pasteObjects(types.manage_copyObjects(['SimpleFolder']))
        types.manage_renameObjects(['copy_of_SimpleFolder'], ['MySimpleFolder'])
        my_type = types['MySimpleFolder']
        attrs = dict(allowed_content_types=('SimpleFolder',),
                     filter_content_types=True,
                     portal_type='MySimpleFolder',
                     title='MySimpleFolder')
        my_type.__dict__.update(attrs)

        browser = Browser()
        browser.addHeader('Authorization',
                          'Basic %s:%s' % ('portal_owner', user_password))
        browser.open(self.folder.absolute_url())
        browser.getLink('Add new').click()
        browser.getControl('MySimpleFolder').click()
        browser.getControl('Add').click()

        browser.getControl('Title').value = 'My dope folder'
        browser.getControl('Save').click()
        self.failUnless('Changes saved.' in browser.contents)
        self.failUnless('My dope folder' in browser.contents)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPermissions))
    suite.addTest(makeSuite(TestFTICopy))
    return suite
