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

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.atapi import BaseSchema, BaseContent, Schema, \
    StringField, registerType, process_types, listTypes
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.VariableSchemaSupport import VariableSchemaSupport

schema = BaseSchema
schema1 = BaseSchema + Schema((StringField('additionalField'),))


class Dummy(VariableSchemaSupport, BaseContent):
    schema = schema


class VarSchemataTest(ATTestCase):

    def afterSetUp(self):
        registerType(Dummy, 'Archetypes')
        content_types, constructors, ftis = process_types(
            listTypes(), PKG_NAME)

    def test_variableschema(self):
        self.folder.dummy = Dummy(oid='dummy')
        dummy = self.folder.dummy
        dummy.setTitle('dummy1')
        self.assertEqual(dummy.Title(), 'dummy1')

        # change the schema
        dummy.schema = schema1
        # try to read an old value using the new schema
        self.assertEqual(dummy.Title(), 'dummy1')
        dummy.setAdditionalField('flurb')
        # check if we can read the new field using the new schema
        self.assertEqual(dummy.getAdditionalField(), 'flurb')
