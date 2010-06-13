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

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore import permissions
from Testing.ZopeTestCase import user_password

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase
from Products.Archetypes.tests.utils import makeContent

# BBB Zope 2.12
try:
    from Testing.testbrowser import Browser
except ImportError:
    from Products.Five.testbrowser import Browser


class TestPermissions(ATSiteTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        # install AT within portal
        self.login()
        self.demo_instances = []
        for t in self.demo_types:
            inst = makeContent(self.folder, portal_type=t, id=t)
            self.demo_instances.append(inst)

    def testPermissions(self):
        for content in self.demo_instances:
            self.failUnless(checkPerm(permissions.View, content))
            self.failUnless(checkPerm(permissions.AccessContentsInformation, content))
            self.failUnless(checkPerm(permissions.ModifyPortalContent, content))

    def testRendering(self):
        # Attempt to call each object and make sure it presents a rendered
        # html view
        for content in self.demo_instances:
            self.failUnless(isinstance(content(), basestring))
            self.failUnless(content().strip().startswith('<!DOCTYPE'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPermissions))
    return suite
