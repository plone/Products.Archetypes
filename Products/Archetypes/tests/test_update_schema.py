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

import sys

from ZPublisher.HTTPRequest import HTTPRequest

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.atapi import TextField, BaseSchema, Schema, BaseContent

from Products.Archetypes.ArchetypeTool import registerType

textfield1 = TextField('TEXTFIELD1', required=True, default='A')

textfield1b = TextField('TEXTFIELD1', required=False, default='A')

textfield2 = TextField('TEXTFIELD2', default='B')

schema1 = BaseSchema + Schema((
    textfield1,
))

schema2 = BaseSchema + Schema((
    textfield1b,
    textfield2,
))


class Dummy1(BaseContent):
    pass


class Dummy2(BaseContent):
    pass


class TestUpdateSchema(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self.attool = self.portal.archetype_tool
        # Calling mkDummyInContext adds content, but also registers
        # our classes and adds a copy of the schema.
        self._dummy1 = mkDummyInContext(
            Dummy1, oid='dummy1', context=self.portal, schema=schema1)
        self._dummy2 = mkDummyInContext(
            Dummy2, oid='dummy2', context=self.portal, schema=schema2)

    def test_instance_schema_is_harmful(self):
        """Show that having a schema in the instance is harmful.

        schema should be a class attribute, not an instance attribute.

        The only thing this really tests is that for AT >= 1.5.2,
        having a schema attribute on the instance is bad.  In earlier
        ATs this is no problem.  Nothing bad happens due to the
        earlier AT code.  But the newer ATs cannot handle older
        content that has had a schema update already.

        So: if you copy this test to an earlier Archetypes and it
        fails, that is okay really.  But in AT >= 1.5.2 it does *not*
        fail and this means that some code needs be added to migrate
        old content.
        """
        dummy = self._dummy1
        self.assertTrue(dummy._isSchemaCurrent())

        # You can make schema an instance attribute if you want (or if
        # you are not careful).
        self.assertFalse('schema' in dummy.__dict__)
        dummy.schema = dummy.__class__.schema
        self.assertTrue('schema' in dummy.__dict__)
        # The schema has not *really* changed:
        self.assertTrue(dummy._isSchemaCurrent())
        # But the damage has been done, as we will show soon.

        # We give the class of our content a different schema.
        dummy.__class__.schema = schema2.copy()
        # Reregister the type.  (Not needed in AT <= 1.5.1)
        registerType(Dummy1, 'Archetypes')
        # We are not testing the _isSchemaCurrent method here, so we
        # can simply cheat to let the object know that its schema is
        # not current anymore.
        dummy._signature = 'bogus'
        self.assertFalse(dummy._isSchemaCurrent())

        # Our class has a TEXTFIELD2, but our content does not now it
        # yet.  It *does* already have the getter for that field.
        dummy.getTEXTFIELD2
        self.assertRaises(KeyError, dummy.getTEXTFIELD2)

        # No problem, we just need to update the schema of the
        # content.  Might as well do that for all objects, as that is
        # what the user will do in practice.
        dummy._updateSchema()

        # And now we can get our second text field, right?  Wrong.
        # Only the getter is there and it does not work.
        self.assertTrue(hasattr(dummy, 'getTEXTFIELD2'))
        # Actually, the next two tests fail for AT <= 1.5.1, which is
        # actually good.
        self.assertRaises(KeyError, dummy.getTEXTFIELD2)
        self.assertFalse(hasattr(dummy, 'TEXTFIELD2'))

        # And the first field was required in the first schema but not
        # in the second.  This does not show yet.
        self.assertTrue(dummy.getField('TEXTFIELD1').required)

        # This can be fixed by deleting the schema attribute of the
        # instance.
        del dummy.schema
        self.assertFalse(dummy.getField('TEXTFIELD1').required)

        # At first, direct attribute access for the second field still
        # does not work:
        self.assertFalse(hasattr(dummy, 'TEXTFIELD2'))
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
        self.assertFalse('schema' in dummy.__dict__)

    def test_detect_schema_change(self):
        dummy = self._dummy1
        self.assertTrue(dummy._isSchemaCurrent())
        dummy.__class__.schema = schema2.copy()
        # Reregister the type.  (Not needed in AT <= 1.5.1)
        registerType(Dummy1, 'Archetypes')
        self.assertFalse(dummy._isSchemaCurrent())
        dummy._updateSchema()
        self.assertTrue(dummy._isSchemaCurrent())

    def test_remove_instance_schemas(self):
        dummy = self._dummy1
        dummy.schema = schema2.copy()
        self.assertTrue('schema' in dummy.__dict__)
        dummy._updateSchema()
        self.assertTrue('schema' in dummy.__dict__)
        dummy._updateSchema(remove_instance_schemas=True)
        self.assertFalse('schema' in dummy.__dict__)

    def test_manage_update_schema(self):
        dummy = self._dummy1
        dummy.schema = schema2.copy()
        self.assertTrue('schema' in dummy.__dict__)
        self.assertFalse(dummy._isSchemaCurrent())

        # Now we want to update all schemas, but first archetype_tool
        # needs to know that our class needs updating.  The easiest of
        # course is to cheat.
        self.assertEqual(self.types_to_update(), [])
        self.attool._types['Archetypes.Dummy1'] = 'cheat'
        self.assertEqual(self.types_to_update(), ['Archetypes.Dummy1'])

        # Now we are ready to call manage_updateSchema
        self.attool.manage_updateSchema()
        # This will have no effect on the schema attribute:
        self.assertTrue('schema' in dummy.__dict__)
        # It *does* wrongly mark the schema as current.
        self.assertTrue(dummy._isSchemaCurrent())
        # So we cheat again and then it works.
        dummy._signature = 'bogus'
        self.assertFalse(dummy._isSchemaCurrent())

        # Let's try again.  But first we cheat again.
        self.assertEqual(self.types_to_update(), [])
        self.attool._types['Archetypes.Dummy1'] = 'cheat'
        self.assertEqual(self.types_to_update(), ['Archetypes.Dummy1'])

        # We need to call manage_updateSchema with an extra option.
        self.attool.manage_updateSchema(remove_instance_schemas=True)
        self.assertFalse('schema' in dummy.__dict__)

    def types_to_update(self):
        """Which types have a changed schema?
        """
        return [ti[0] for ti in self.attool.getChangedSchema() if ti[1]]


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
                              {'SERVER_NAME': 'test', 'SERVER_PORT': '8080'},
                              {})
        request.form['Archetypes.DDocument'] = True
        request.form['update_all'] = True
        self.portal.archetype_tool.manage_updateSchema(REQUEST=request)
        doc = self.folder.mydoc
        mimetype = doc.getField('body').getContentType(doc)
        self.assertEqual(mimetype, 'text/x-rst')
