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

from Products.Archetypes.Storage import AttributeStorage, MetadataStorage, MySQLStorage
from test_classgen import ClassGenTest, Dummy
from DateTime import DateTime

class ChangeStorageTest( unittest.TestCase ):
    def setUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = dummy = Dummy(oid='dummy')
        self._old_storages = {}
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.name] = field.getStorage()

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
        
        for field in dummy.type.fields():
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
        
    def tearDown(self):
        dummy = self._dummy
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, self._old_storages[field.name])

class MetadataStorageTest( ClassGenTest ):

    def setUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = dummy = Dummy(oid='dummy')
        self._old_storages = {}
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.name] = field.getStorage()
                field.setStorage(dummy, MetadataStorage())

    def tearDown(self):
        dummy = self._dummy
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, self._old_storages[field.name])

class AttributeStorageTest( ClassGenTest ):

    def setUp( self ):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = dummy = Dummy(oid='dummy')
        self._old_storages = {}
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.name] = field.getStorage()
                field.setStorage(dummy, AttributeStorage())

    def tearDown(self):
        dummy = self._dummy
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, self._old_storages[field.name])


class SQLStorageTest( ClassGenTest ):

    def setUp( self ):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = dummy = Dummy(oid='dummy')
        self._old_storages = {}
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                self._old_storages[field.name] = field.getStorage()
                field.setStorage(dummy, MySQLStorage())

    def tearDown(self):
        dummy = self._dummy
        for field in dummy.type.fields():
            if field.name in ['atextfield', 'adatefield', 'alinesfield', 'anobjectfield']:
                field.setStorage(dummy, self._old_storages[field.name])

        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MetadataStorageTest),
        unittest.makeSuite(AttributeStorageTest),
        unittest.makeSuite(ChangeStorageTest),
        ))

if __name__ == '__main__':
    unittest.main()
