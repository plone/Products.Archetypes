# -*- coding: UTF-8 -*-
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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.schemata import Schemata, getNames
from Products.Archetypes.schemata.variable import VariableSchemaSupport

from DateTime import DateTime

schema = BaseSchema
schema1= BaseSchema + Schema((StringField('additionalField'),))

class Dummy(VariableSchemaSupport,BaseContent):
    schema = schema


class VarSchemataTest( ArchetypesTestCase ):

    def afterSetUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')

    def test_variableschema(self):

        dummy = self._dummy
        dummy.update(id='dummy1')
        self.assertEqual(dummy.getId(),'dummy1')

        #change the schema
        dummy.schema=schema1
        #try to read an old value using the new schema
        self.assertEqual(dummy.getId(),'dummy1')
        dummy.update(additionalField='flurb')
        #check if we can read the new field using the new schema
        self.assertEqual(dummy.getAdditionalField(),'flurb')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(VarSchemataTest))
    return suite

if __name__ == '__main__':
    framework()
