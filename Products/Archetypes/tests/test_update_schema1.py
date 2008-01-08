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

import os
import sys

from ZPublisher.HTTPRequest import HTTPRequest
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

import shutil

from Products.CMFCore.utils import getToolByName

# ArchetypesTestUpdateSchema does not work on Zope 2.8 or higher
hasATTUS = False

# We are breaking up the update schema test into 2 separate parts, since
# the product refresh appears to cause strange things to happen when we
# run multiple tests in the same test suite.

class TestUpdateSchema1(ZopeTestCase.Sandboxed, ATSiteTestCase):

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


    def test_detect_schema_change(self):
        self._setClass(1)

        t1 = makeContent(self.folder, portal_type='TestClass', id='t1')
        self.failUnless(t1._isSchemaCurrent())

        self.portal.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())

        self._setClass(2)

        t1 = self.folder.t1
        self.failIf(t1._isSchemaCurrent())

        t2 = makeContent(self.folder, portal_type='TestClass', id='t2')
        self.failUnless(t2._isSchemaCurrent())

        self.portal.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())


class TestBasicSchemaUpdate(ATSiteTestCase):
    """Tests for update schema behavior which depend only on the basic
       types, and examine baseline behavior when no real schema changes have
       happened."""

    def test_update_preserves_tyoe(self):
        self.folder.invokeFactory('DDocument', 'mydoc', title="My Doc")
        doc = self.folder.mydoc
        doc.setBody("""
An rst Document
===============

* Which

  * has

  * some

* bullet::

  points.

* for testing""",  mimetype="text/restructured")
        doc.reindexObject()
        mimetype = doc.getField('body').getContentType(doc)
        self.assertEqual(mimetype, 'text/x-rst')

        # update schema for all DDocuments and check if our type is preserved
        request = HTTPRequest(sys.stdin,
                              {'SERVER_NAME':'test', 'SERVER_PORT': '8080'},
                              {})
        request.form['Archetypes.DDocument'] = True
        request.form['update_all'] = True
        self.portal.archetype_tool.manage_updateSchema(REQUEST=request)
        doc = self.folder.mydoc
        mimetype = doc.getField('body').getContentType(doc)
        self.assertEqual(mimetype, 'text/x-rst')



def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if hasATTUS:
        suite.addTest(makeSuite(TestUpdateSchema1))
    suite.addTest(makeSuite(TestBasicSchemaUpdate))
    return suite
