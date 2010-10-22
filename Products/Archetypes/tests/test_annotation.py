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

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.atapi import *
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_class
from Products.Archetypes.tests.test_classgen import gen_dummy
from Acquisition import aq_base

class AnnDummy(Dummy): pass

annschema = BaseSchema + Schema((
     StringField('string',
         default = u'stringdefault',
         storage = AnnotationStorage(),
         ),
     StringField('meta',
         default = 'metadefault',
         storage = MetadataAnnotationStorage(),
         ),
    ))


def gen_anndummy():
    gen_class(AnnDummy, annschema)

class AnnotationTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_dummy()
        dummy = Dummy(oid='dummy')
        self.folder._setObject('dummy', dummy)
        self.folder.dummy.initializeArchetype()
        self.dummy = self.folder.dummy
        self.ann = getAnnotation(self.dummy)

    def test_empty(self):
        ann = self.ann
        self.failUnlessEqual(bool(ann), False)
        self.failUnlessEqual(getattr(self.dummy, '__annotations__', None), None)

    def test_create(self):
        ann = self.ann
        ann['test'] = 'test'
        self.failUnlessEqual(bool(ann), True)
        self.failIfEqual(getattr(self.dummy, '__annotations__', None), None)

    def test_set(self):
        ann = self.ann
        ann['test'] = 'test1'
        self.failUnlessEqual(ann['test'], 'test1')
        ann.set('test', 'test2')
        self.failUnlessEqual(ann['test'], 'test2')
        ann.setSubkey('test', 'test3', subkey='testsub')
        self.failUnlessEqual(ann['test-testsub'], 'test3')
        self.failUnlessEqual(ann.getSubkey('test', subkey='testsub'), 'test3')

    def test_get(self):
        ann = self.ann
        ann['test'] = 'test1'
        self.failUnlessEqual(ann['test'], 'test1')
        self.failUnlessEqual(ann.get('test'), 'test1')
        self.failUnless(ann.has_key('test'))
        self.failUnlessEqual(ann.get('none', default='default'), 'default')

    def test_del(self):
        ann = self.ann
        ann['test'] = 'test1'
        del ann['test']
        self.failIf(ann.has_key('test'))
        ann.setSubkey('test', 'test3', subkey='testsub')
        ann.delSubkey('test', subkey='testsub')
        self.failIf(ann.has_key('test-testsub'))
        self.failIf(ann.hasSubkey('test', subkey='testsub'))


class MetadataAnnotationStorageTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_anndummy()
        dummy = AnnDummy(oid='dummy')
        self.folder._setObject('dummy', dummy)
        self.dummy = self.folder.dummy
        self.dummy.initializeArchetype()
        self.ann = getAnnotation(self.dummy)

    def test_setup(self):
        dummy = self.dummy
        field = dummy.getField('meta')
        self.failUnless(isinstance(field.storage, MetadataAnnotationStorage))
        self.failUnless(self.ann.hasSubkey(AT_MD_STORAGE, 'meta'))
        self.failUnlessEqual(self.ann.getSubkey(AT_MD_STORAGE, subkey='meta'), 'metadefault')

    def test_gestset(self):
        dummy = self.dummy
        ann = self.ann
        dummy.setMeta('egg')
        self.failUnlessEqual(dummy.getMeta(), 'egg')
        self.failUnlessEqual(ann.getSubkey(AT_MD_STORAGE, subkey='meta'), 'egg')

class AnnotationStorageTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_anndummy()
        dummy = AnnDummy(oid='dummy')
        self.folder._setObject('dummy', dummy)
        self.dummy = self.folder.dummy
        self.dummy.initializeArchetype()
        self.ann = getAnnotation(self.dummy)

    def test_setup(self):
        dummy = self.dummy
        field = dummy.getField('string')
        self.failUnless(isinstance(field.storage, AnnotationStorage))
        self.failUnless(self.ann.hasSubkey(AT_ANN_STORAGE, 'string'))
        self.failUnlessEqual(self.ann.getSubkey(AT_ANN_STORAGE, subkey='string'), 'stringdefault')

    def test_gestset(self):
        dummy = self.dummy
        ann = self.ann
        dummy.setString('egg')
        self.failUnlessEqual(dummy.getString(), 'egg')
        self.failUnlessEqual(ann.getSubkey(AT_ANN_STORAGE, subkey='string'), 'egg')

    def test_storageGetSetDel(self):
        dummy = self.dummy
        ann = self.ann
        field = dummy.getField('string')
        storage = field.storage

        dummy.setString('egg')
        self.failUnlessEqual(storage.get('string', dummy), 'egg')

        storage.set('string', dummy, 'spam')
        self.failUnlessEqual(storage.get('string', dummy), 'spam')

        storage.unset('string', dummy)
        self.failIf(ann.hasSubkey(AT_ANN_STORAGE, 'string'))

    def test_storageNonExisting(self):
        dummy = self.dummy
        ann = self.ann
        storage = AnnotationStorage()

        self.failUnlessRaises(AttributeError, storage.get, 'nonexisting', dummy)

        # del shouldn't raise anything
        storage.unset('nonexisting', dummy)

        # set should create an entry
        storage.set('nonexisting', dummy,  value='bar')
        self.failUnlessEqual(storage.get('nonexisting', dummy), 'bar')

    def test_migration(self):
        dummy = self.dummy
        ann = self.ann
        field = dummy.getField('string')
        storage = field.storage

        # migration mode on
        self.failUnlessEqual(storage._migrate, False)
        storage._migrate = True

        # test clean up
        dummy.string = 'spam'
        self.failUnless(hasattr(aq_base(dummy), 'string'))

        self.failIfEqual(storage.get('string', dummy), 'spam')
        storage.set('string', dummy, 'bar')
        self.failIf(hasattr(aq_base(dummy), 'string'))
        self.failUnlessEqual(storage.get('string', dummy), 'bar')

        # test migration
        ann.delSubkey(AT_ANN_STORAGE, subkey='string')
        dummy.string = 'spam'
        self.failUnlessEqual(storage.get('string', dummy), 'spam')
        self.failIf(hasattr(aq_base(dummy), 'string'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(AnnotationTest))
    suite.addTest(makeSuite(MetadataAnnotationStorageTest))
    suite.addTest(makeSuite(AnnotationStorageTest))
    return suite
