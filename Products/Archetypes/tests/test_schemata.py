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

import operator

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.atapi import BaseSchema, BaseContent, registerType, \
    process_types, listTypes, StringWidget
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Schema import Schemata
from Products.Archetypes.Schema import getNames
from Products.Archetypes.Field import StringField
from Products.Archetypes.exceptions import SchemaException
from Products.CMFCore.permissions import ModifyPortalContent

schema = BaseSchema


class Dummy(BaseContent):
    schema = schema


class SchemataTest(ATSiteTestCase):

    def afterSetUp(self):
        registerType(Dummy, 'Archetypes')
        content_types, constructors, ftis = process_types(
            listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')

    def test_availschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        keys = schemata.keys()
        keys.sort()
        self.assertEqual(keys, ['default', 'metadata'])

    def test_nameschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        self.assertEqual(schemata['default'].getName(), 'default')
        self.assertEqual(schemata['metadata'].getName(), 'metadata')

    def test_baseschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        base_names = getNames(schemata['default'])
        self.assertEqual(base_names, ['id', 'title'])

    def test_metaschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        meta_names = getNames(schemata['metadata'])
        self.assertEqual(meta_names, ['allowDiscussion', 'subject',
                                      'description', 'location', 'contributors',
                                      'creators', 'effectiveDate',
                                      'expirationDate', 'language',
                                      'rights', 'creation_date',
                                      'modification_date'])

    def test_dupe_accessor_names_add(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        b = Schemata(fields=(StringField('bar',
                                         accessor='getSomething',
                                         edit_accessor='editThat',
                                         mutator='setThat',
                                         ),))
        self.assertRaises(SchemaException, operator.add, a, b)

    def test_dupe_edit_accessor_names_add(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        b = Schemata(fields=(StringField('bar',
                                         accessor='getThat',
                                         edit_accessor='editSomething',
                                         mutator='setThat',
                                         ),))
        self.assertRaises(SchemaException, operator.add, a, b)

    def test_dupe_mutator_names_add(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        b = Schemata(fields=(StringField('bar',
                                         accessor='getThat',
                                         edit_accessor='editThat',
                                         mutator='setSomething',
                                         ),))
        self.assertRaises(SchemaException, operator.add, a, b)

    def test_dupe_primary_add(self):
        a = Schemata(fields=(StringField('foo', primary=True),))
        b = Schemata(fields=(StringField('bar', primary=True),))
        self.assertRaises(SchemaException, operator.add, a, b)

    def test_dupe_accessor_names_addField(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        field = StringField('bar',
                            accessor='getSomething',
                            edit_accessor='editThat',
                            mutator='setThat',
                            )
        self.assertRaises(SchemaException, a.addField, field)

    def test_dupe_edit_accessor_names_addField(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        field = StringField('bar',
                            accessor='getThat',
                            edit_accessor='editSomething',
                            mutator='setThat',
                            )
        self.assertRaises(SchemaException, a.addField, field)

    def test_dupe_mutator_names_addField(self):
        a = Schemata(fields=(StringField('foo',
                                         accessor='getSomething',
                                         edit_accessor='editSomething',
                                         mutator='setSomething',
                                         ),))
        field = StringField('bar',
                            accessor='getThat',
                            edit_accessor='editThat',
                            mutator='setSomething',
                            )
        self.assertRaises(SchemaException, a.addField, field)

    def test_dupe_primary_addField(self):
        a = Schemata(fields=(StringField('foo', primary=True),))
        field = StringField('bar', primary=True)
        self.assertRaises(SchemaException, a.addField, field)

    def test_editableFields(self):
        # Not a security test, but this is here because 'editableFields'
        # will return only fields the user is allowed to write.
        dummy = self._dummy.__of__(self.folder)
        self.setRoles(['Manager'])
        dummy.manage_permission(ModifyPortalContent, roles=['Manager'])

        # add test fields to schema
        fields = (
            StringField(
                'f1',
                mutator='setF1',
                write_permission=ModifyPortalContent,
                widget=StringWidget(visible={'edit': 'invisible'}),
            ),
            StringField('f2',
                        mutator='setF2',
                        write_permission=ModifyPortalContent,
                        widget=StringWidget(visible={'edit': 'hidden'}),
                        ),
            StringField('f3',
                        mutator='setF3',
                        write_permission=ModifyPortalContent,
                        widget=StringWidget(condition='python:False',),
                        ),
        )

        for f in fields:
            dummy.schema.addField(f)

        # add dummy mutators to pass the test in 'editableFields'
        def dummy_mutator(instance, value):
            pass

        dummy.setF1 = dummy_mutator
        dummy.setF2 = dummy_mutator
        dummy.setF3 = dummy_mutator

        # get editable fields
        schemata = dummy.Schemata()['default']
        editable_field_ids = [f.getName() for f in
                              schemata.editableFields(dummy, visible_only=True)]

        self.assertTrue('f1' not in editable_field_ids)
        self.assertTrue('f2' in editable_field_ids)
        self.assertTrue('f3' not in editable_field_ids)
