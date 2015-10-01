##########################################################################
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
##########################################################################

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore import permissions

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.tests.utils import makeContent


class TestPermissions(ATTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    def afterSetUp(self):
        ATTestCase.afterSetUp(self)
        # install AT within portal
        self.login()
        self.demo_instances = []
        for t in self.demo_types:
            inst = makeContent(self.folder, portal_type=t, id=t)
            self.demo_instances.append(inst)

    def testPermissions(self):
        for content in self.demo_instances:
            self.assertTrue(checkPerm(permissions.View, content))
            self.assertTrue(
                checkPerm(permissions.AccessContentsInformation, content))
            self.assertTrue(
                checkPerm(permissions.ModifyPortalContent, content))

    def testRendering(self):
        # Attempt to call each object and make sure it presents a rendered
        # html view
        for content in self.demo_instances:
            self.assertTrue(isinstance(content(), basestring))
            self.assertTrue(content().strip().startswith('<!DOCTYPE'))
