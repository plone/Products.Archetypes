import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.config import ZOPE_LINES_IS_TUPLE_TYPE
from Products.Archetypes import listTypes
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
