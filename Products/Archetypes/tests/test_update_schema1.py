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
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.atapi import *

import shutil

from Products.CMFCore.utils import getToolByName
#from Products.Archetypes.BaseObject import BaseObject

textfield1 = TextField('TEXTFIELD1', primary=True, default='A')

textfield2 = TextField('TEXTFIELD2', primary=False, default='B')

textfield3 = TextField('TEXTFIELD3', primary=False, default='C')

schema1 = BaseSchema + Schema((
        textfield1,
        ))

schema2 = BaseSchema + Schema((
        textfield1,
        textfield2,
        ))

schema3 = BaseSchema + Schema((
        textfield1,
        textfield3,
        ))

class Dummy1(BaseContent):
    pass


class Dummy2(BaseContent):
    pass


class Dummy3(BaseContent):
    pass


class TestUpdateSchema(ZopeTestCase.Sandboxed, ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        # Calling mkDummyInContext adds content, but also registers
        # our classes and adds a copy of the schema.
        self._dummy1 = mkDummyInContext(
            Dummy1, oid='dummy', context=self.portal, schema=schema1)
        self._dummy2 = mkDummyInContext(
            Dummy2, oid='dummy', context=self.portal, schema=schema2)
        self._dummy3 = mkDummyInContext(
            Dummy3, oid='dummy', context=self.portal, schema=schema3)

    def test_instance_schema_is_harmful(self):
        """Show that having a schema in the instance is harmful.

        schema should be a class attribute, not an instance attribute.
        """
        dummy = self._dummy1
        self.failUnless(dummy._isSchemaCurrent())

        # You can make schema an instance attribute if you want (or if
        # you are not careful).
        self.failIf('schema' in dummy.__dict__)
        dummy.schema = dummy.__class__.schema
        self.failUnless('schema' in dummy.__dict__)
        # The schema has not *really* changed:
        self.failUnless(dummy._isSchemaCurrent())
        # But the damage has been done, as we will show soon.

        # We give the class of our content a different schema.  The
        # only sane/working way is to actually change the class.
        dummy.__class__ = Dummy2
        # Naturally, the schema of our content is not current anymore.
        # XXX Ehm, actually... this fails:
        #self.failIf(dummy._isSchemaCurrent())

        # Our class has a TEXTFIELD2, but our content does not now it
        # yet.  It *does* already have the getter for that field.
        dummy.getTEXTFIELD2
        self.assertRaises(KeyError, dummy.getTEXTFIELD2)

        # No problem, we just need to update the schema of the
        # content.
        dummy._updateSchema()

        # And now we can get our text field, right?  Wrong.
        # Only the getter is there and it does not work.
        self.failUnless(hasattr(dummy, 'getTEXTFIELD2'))
        self.assertRaises(KeyError, dummy.getTEXTFIELD2)
        self.failIf(hasattr(dummy, 'TEXTFIELD2'))

        # This can be fixed by deleting the schema attribute of the
        # instance.
        del dummy.schema

        # At first, direct attribute access still does not work:
        self.failIf(hasattr(dummy, 'TEXTFIELD2'))
        # But calling the getter works.
        self.assertEqual(dummy.getTEXTFIELD2(), 'B')
        # And after that call, direct attribute access works too.
        self.assertEqual(dummy.TEXTFIELD2(), 'B')
        # Note: TEXTFIELD is a BaseUnit, which means you need to call
        # it to get its value.
        
    def test_no_schema_attribute_added(self):
        """Does updating the schema mess things up?

        Updating the schema should not add the schema as instance
        attribute, unless you *really* know what you are doing.
        """
        dummy = self._dummy1
        dummy._updateSchema()
        self.failIf('schema' in dummy.__dict__)

    def test_detect_schema_change(self):
        dummy = self._dummy1
        self.failUnless(dummy._isSchemaCurrent())
        dummy.__class__.schema = schema2.copy()
        self.failIf(dummy._isSchemaCurrent())
        dummy._updateSchema()
        self.failUnless(dummy._isSchemaCurrent())


class TestBasicSchemaUpdate(ATSiteTestCase):
    """Tests for update schema behavior which depend only on the basic
       types, and examine baseline behavior when no real schema changes have
       happened."""

    def test_update_preserves_mimetype(self):
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
    suite.addTest(makeSuite(TestUpdateSchema))
    suite.addTest(makeSuite(TestBasicSchemaUpdate))
    return suite
