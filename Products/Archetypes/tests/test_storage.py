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
"""
"""

from Products.Archetypes.atapi import AttributeStorage, MetadataStorage

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy


class ChangeStorageTest(ATTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        self._old_storages = {}

    def test_changestorage(self):
        dummy = self._dummy
        dummy.setAtextfield('sometext', mimetype="text/plain")
        dummy.setAdatefield('2003-01-01')
        dummy.setAlinesfield(['bla', 'bla', 'bla'])
        dummy.setAnobjectfield('someothertext')

        out = ('bla', 'bla', 'bla')

        self.assertEqual(str(dummy.getAtextfield()), 'sometext')
        self.assertTrue(dummy.getAdatefield().ISO8601(
        ).startswith('2003-01-01T00:00:00'))
        self.assertEqual(dummy.getAlinesfield(), out)
        self.assertEqual(dummy.getAnobjectfield(), 'someothertext')

        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.getName()] = field.getStorage()
                field.setStorage(dummy, AttributeStorage())
                self.assertEqual(field.getStorage().getName(),
                                 'AttributeStorage')
                field.setStorage(dummy, MetadataStorage())
                self.assertEqual(field.getStorage().getName(),
                                 'MetadataStorage')

        self.assertEqual(str(dummy.getAtextfield()), 'sometext')
        self.assertTrue(dummy.getAdatefield().ISO8601(
        ).startswith('2003-01-01T00:00:00'))
        self.assertEqual(dummy.getAlinesfield(), out)
        self.assertEqual(dummy.getAnobjectfield(), 'someothertext')

    def test_unset(self):
        dummy = self._dummy
        dummy.setAtextfield('sometext')
        field = dummy.getField('atextfield')
        field.setStorage(dummy, AttributeStorage())
        self.assertTrue(hasattr(dummy, 'atextfield'))
        field.setStorage(dummy, MetadataStorage())
        self.assertFalse(hasattr(dummy, 'atextfield'))
        self.assertTrue('atextfield' in dummy._md)
        field.setStorage(dummy, AttributeStorage())
        self.assertTrue('atextfield' not in dummy._md)
        self.assertTrue(hasattr(dummy, 'atextfield'))


class MetadataStorageTest(ATTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, MetadataStorage())


class AttributeStorageTest(ATTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, AttributeStorage())
