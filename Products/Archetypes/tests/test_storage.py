# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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
from Products.Archetypes.config import ZOPE_LINES_IS_TUPLE_TYPE
from Products.Archetypes.storages import AttributeStorage, MetadataStorage
from test_classgen import ClassGenTest, Dummy, gen_dummy

from DateTime import DateTime


class ChangeStorageTest( ArchetypesTestCase ):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        self._old_storages = {}

    def test_changestorage(self):
        dummy = self._dummy
        dummy.setAtextfield('sometext', mimetype="text/plain")
        dummy.setAdatefield('2003-01-01')
        dummy.setAlinesfield(['bla','bla','bla'])
        dummy.setAnobjectfield('someothertext')

        if ZOPE_LINES_IS_TUPLE_TYPE:
            out = ('bla','bla','bla')
        else:
            out = ['bla','bla','bla']

        self.failUnlessEqual(str(dummy.getAtextfield()), 'sometext')
        self.failUnlessEqual(dummy.getAdatefield(), DateTime('2003-01-01'))
        self.failUnlessEqual(dummy.getAlinesfield(), out)
        self.failUnlessEqual(dummy.getAnobjectfield(), 'someothertext')

        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.getName()] = field.getStorage()
                field.setStorage(dummy, AttributeStorage())
                self.failUnlessEqual(field.getStorage().getName(), 'AttributeStorage')
                field.setStorage(dummy, MetadataStorage())
                self.failUnlessEqual(field.getStorage().getName(), 'MetadataStorage')

        self.failUnlessEqual(str(dummy.getAtextfield()), 'sometext')
        self.failUnlessEqual(dummy.getAdatefield(), DateTime('2003-01-01'))
        self.failUnlessEqual(dummy.getAlinesfield(), out)
        self.failUnlessEqual(dummy.getAnobjectfield(), 'someothertext')

    def test_unset(self):
        dummy = self._dummy
        dummy.setAtextfield('sometext')
        field = dummy.getField('atextfield')
        field.setStorage(dummy, AttributeStorage())
        self.failUnless(hasattr(dummy, 'atextfield'))
        field.setStorage(dummy, MetadataStorage())
        self.failIf(hasattr(dummy, 'atextfield'))
        self.failUnless(dummy._md.has_key('atextfield'))
        field.setStorage(dummy, AttributeStorage())
        self.failIf(dummy._md.has_key('atextfield'))
        self.failUnless(hasattr(dummy, 'atextfield'))


class MetadataStorageTest( ArchetypesTestCase ):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, MetadataStorage())


class AttributeStorageTest( ArchetypesTestCase ):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        for field in dummy.schema.fields():
            if field.getName() in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, AttributeStorage())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ChangeStorageTest))
    suite.addTest(makeSuite(MetadataStorageTest))
    suite.addTest(makeSuite(AttributeStorageTest))
    return suite

if __name__ == '__main__':
    framework()

