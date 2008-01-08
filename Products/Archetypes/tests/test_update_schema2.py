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
"""


import os
import shutil
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.CMFCore.utils import getToolByName

# ArchetypesTestUpdateSchema does not work on Zope 2.8 or higher
hasATTUS = False

# We are breaking up the update schema test into 2 separate parts, since
# the product refresh appears to cause strange things to happen when we
# run multiple tests in the same test suite.

class TestUpdateSchema2(ZopeTestCase.Sandboxed, ATSiteTestCase):

    def afterSetUp(self):
        qi = getToolByName(self.portal, 'portal_quickinstaller')
        qi.installProduct('ArchetypesTestUpdateSchema')

    def _setClass(self, version):
        import Products.ArchetypesTestUpdateSchema
        classdir = Products.ArchetypesTestUpdateSchema.getDir()
        dest = os.path.join(classdir, 'TestClass.py')
        pyc = os.path.join(classdir, 'TestClass.pyc')
        src = os.path.join(classdir, 'TestClass%d.py' % version)
        shutil.copyfile(src, dest)
        os.utime(dest,None)
        try:
            os.remove(pyc)
        except:
            pass

        self.app.Control_Panel.Products.ArchetypesTestUpdateSchema.manage_performRefresh()

    def test_update_schema(self):
        self._setClass(1)

        t1 = makeContent(self.folder, portal_type='TestClass', id='t1')

        self.failUnless(hasattr(t1, 'a'))
        self.failUnless(t1.Schema().get('a').required == 0)
        self.failIf(hasattr(t1, 'b'))

        self.portal.archetype_tool.manage_updateSchema()

        self.failUnless(hasattr(t1, 'a'))
        self.failIf(hasattr(t1, 'b'))

        self._setClass(2)

        t2 = makeContent(self.folder, portal_type='TestClass', id='t2')
        self.failUnless(hasattr(t2, 'a'))
        self.failUnless(hasattr(t2, 'b'))

        t1 = self.folder.t1

        self.failUnless(hasattr(t1, 'a'))
        self.failUnless(t1.Schema().get('a').required == 0)
        self.failIf(hasattr(t1, 'b'))

        # update schema
        self.portal.archetype_tool.manage_updateSchema()

        self.failUnless(hasattr(t1, 'a'))
        self.failUnless(t1.Schema().get('a').required == 1)
        self.failUnless(hasattr(t1, 'b'))
        self.failUnless(hasattr(t1, 'getA'))
        self.failUnless(hasattr(t1, 'getB'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if hasATTUS:
        suite.addTest(makeSuite(TestUpdateSchema2))
    return suite
