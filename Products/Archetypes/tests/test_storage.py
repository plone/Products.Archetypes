import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

import unittest

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import listTypes
from Products.Archetypes.Storage import AttributeStorage, MetadataStorage
from test_classgen import ClassGenTest, Dummy, gen_dummy

from DateTime import DateTime

class ChangeStorageTest( unittest.TestCase ):
    def setUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initalizeArchetype()
        self._old_storages = {}

    def test_changestorage(self):
        dummy = self._dummy
        dummy.setAtextfield('sometext')
        dummy.setAdatefield('2003-01-01')
        dummy.setAlinesfield(['bla','bla','bla'])
        dummy.setAnobjectfield('someothertext')

        self.failUnless(str(dummy.getAtextfield()) == 'sometext')
        self.failUnless(dummy.getAdatefield() == DateTime('2003-01-01'))
        self.failUnless(dummy.getAlinesfield() == ['bla','bla','bla'])
        self.failUnless(dummy.getAnobjectfield() == 'someothertext')
        
        for field in dummy.schema.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.name] = field.getStorage()
                field.setStorage(dummy, AttributeStorage())
                self.failUnless(field.getStorage().getName() == 'AttributeStorage')
                field.setStorage(dummy, MetadataStorage())
                self.failUnless(field.getStorage().getName() == 'MetadataStorage')

        self.failUnless(str(dummy.getAtextfield()) == 'sometext')
        self.failUnless(dummy.getAdatefield() == DateTime('2003-01-01'))
        self.failUnless(dummy.getAlinesfield() == ['bla','bla','bla'])
        self.failUnless(dummy.getAnobjectfield() == 'someothertext')

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
        

class MetadataStorageTest( ClassGenTest ):

    def setUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initalizeArchetype()
        for field in dummy.schema.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, MetadataStorage())


class AttributeStorageTest( ClassGenTest ):

    def setUp( self ):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initalizeArchetype()
        for field in dummy.schema.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, AttributeStorage())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ChangeStorageTest),
        unittest.makeSuite(MetadataStorageTest),
        unittest.makeSuite(AttributeStorageTest),
        ))

if __name__ == '__main__':
    unittest.main()
