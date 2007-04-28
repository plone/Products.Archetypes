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

import os, sys
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME
from Products.Archetypes.tests.utils import makeContent

import transaction
from zExceptions.ExceptionFormatter import format_exception

def pretty_exc(self, exc, *args, **kw):
    t, e, tb = exc
    try:
        return ''.join(format_exception(t, e, tb, format_src=1))
    except:
        return ''.join(format_exception(t, e, tb))

import unittest
unittest.TestResult._exc_info_to_string = pretty_exc

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes import SQLStorage
from Products.Archetypes import SQLMethod
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.tests.utils import Dummy

from DateTime import DateTime

# the id to use in the connection objects
connection_id = 'sql_connection'

# the db names and Connection strings
connectors = {}

# aditional cleanup
cleanup = {}


# Gadfly

# XXX: Gadfly no longer works in Zope 2.7.8/2.8.2
# See http://www.zope.org/Collectors/Zope/556
# We may get around this by avoiding NULL in SQLStorage,
# but for now I am disabling the tests. [shh]
#
#try:
#    from Products.ZGadflyDA.DA import Connection
#except ImportError:
#    print >>sys.stderr, 'Failed to import ZGadflyDA'
#else:
#    ZopeTestCase.installProduct('ZGadflyDA', 0)
#    connectors['Gadfly'] = 'demo'

# Postgresql

try:
    from Products.ZPsycopgDA.DA import Connection
except ImportError:
    print >>sys.stderr, 'Failed to import ZPsycopgDA'
else:
    ZopeTestCase.installProduct('ZPsycopgDA', 0)
    connectors['Postgre'] = 'dbname=demo user=demo host=gandalf'

# MySQL

try:
    from Products.ZMySQLDA.DA import Connection
except ImportError:
    print >>sys.stderr, 'Failed to import ZMySQLDA'
else:
    ZopeTestCase.installProduct('ZMySQLDA', 0)
    transactional = 1 # needs INNODB!
    if transactional:
        connectors['MySQL'] = '+demo@gandalf demo'
    else:
        connectors['MySQL'] = '-demo@gandalf demo'
        def cleanupMySQL(self):
            instance = self._dummy
            args = {}
            args['table'] = 'Dummy'
            storage = self._storage_class
            method = SQLMethod(instance)
            method.edit(connection_id, ' '.join(args.keys()),
                        storage.query_drop)
            query, result = method(test__=1, **args)
        cleanup['MySQL'] = cleanupMySQL


def gen_dummy(storage_class):

    Dummy.schema = BaseSchema + Schema((

        ObjectField(
        'aobjectfield',
        storage = storage_class()
        ),

        StringField(
        'astringfield',
        storage = storage_class()
        ),

        TextField(
        'atextfield',
        storage = storage_class()
        ),

        DateTimeField(
        'adatetimefield',
        storage = storage_class()
        ),

        LinesField(
        'alinesfield',
        storage = storage_class()
        ),

        IntegerField(
        'aintegerfield',
        storage = storage_class()
        ),

        FloatField(
        'afloatfield',
        storage = storage_class()
        ),

        FixedPointField(
        'afixedpointfield',
        storage = storage_class()
        ),

## Xiru: The new reference engine is not SQLStorage aware!

##         ReferenceField(
##         'areferencefield',
##         storage = storage_class()
##         ),

        BooleanField(
        'abooleanfield',
        storage = storage_class()
        ),

## Xiru: SQLStorage does not support the field types below. For
## FileField, use ObjectManagedStorage or AttributeStorage and for
## ImageField and PhotoField use AttributeStorage. They are complex
## object and persist their content in a RDBMS is not a trivial task
## (at lest, not without break a lot of things).

##         FileField(
##         'afilefield',
##         storage = storage_class()
##         ),

##         ImageField(
##         'aimagefield',
##         storage = storage_class()
##         ),

##         PhotoField(
##         'aphotofield',
##         storage = storage_class()
##         ),

    ))

    registerType(Dummy, PKG_NAME)

    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)


def commonAfterSetUp(self):

    portal = self.portal

    # create the Database Adaptor (DA)
    if self.db_name == 'Postgre':
        portal.manage_addProduct['ZPsycopgDA'].manage_addZPsycopgConnection(
            id = connection_id, title = 'PostgreSQL Archetypes Storage',
            connection_string = connectors[self.db_name], zdatetime = 1, check = 1)
    elif self.db_name == 'MySQL':
        portal.manage_addProduct['ZMySQLDA'].manage_addZMySQLConnection(
            id = connection_id, title = 'MySQL Archetypes Storage',
            connection_string = connectors[self.db_name], check = 1)
    elif self.db_name == 'Gadfly':
        portal.manage_addProduct['ZGadflyDA'].manage_addZGadflyConnection(
            id = connection_id, title = 'Gadfly Archetypes Storage',
            connection = connectors[self.db_name], check = 1)

    # add type information for Dummy
    tt = portal.portal_types
    tt.manage_addTypeInformation(
        FactoryTypeInformation.meta_type,
        id = 'Dummy',
        typeinfo_name = 'CMFDefault: Document')

    # set archetype_tool default connection
    at = getToolByName(portal, TOOL_NAME)
    at.setDefaultConn(connection_id)

    # create storage instance and schema
    storage_class = getattr(SQLStorage, self.db_name + 'SQLStorage')
    gen_dummy(storage_class)
    self._storage_class = storage_class

    # create a object instance
    obj = Dummy(oid = 'dummy')
    portal._setObject('dummy', obj)
    obj = getattr(portal, 'dummy')
    self._dummy = obj

    # set meta_type for renaming
    obj.__factory_meta_type__ = 'Archetypes Content'   # Is It really needed?
    obj.meta_type = 'Archetypes Content'


class GadflyMagic:
    """ Make Gadfly tests work out of the box """

    gadfly_dir = os.path.join(PACKAGE_HOME, 'gadfly')
    demo_dir = os.path.join(gadfly_dir, 'demo')

    def afterSetUp(self):
        # Patch Gadfly to work off the temp dir
        from Products.ZGadflyDA import db
        self._data_dir = db.data_dir
        db.data_dir = self.gadfly_dir
        # Create Gadfly database
        os.mkdir(self.gadfly_dir)
        os.mkdir(self.demo_dir)

    def afterClear(self):
        # Restore Gadfly config
        if hasattr(self, '_data_dir'):
            from Products.ZGadflyDA import db
            db.data_dir = self._data_dir
        # Remove Gadfly database
        if os.path.isdir(self.gadfly_dir):
            import shutil
            shutil.rmtree(self.gadfly_dir, 1)


class SQLStorageTestBase(GadflyMagic, ATSiteTestCase):
    """ Abstract base class for the tests """

    db_name = ''
    cleanup = cleanup

    def afterSetUp(self):
        GadflyMagic.afterSetUp(self)
        commonAfterSetUp(self)

    def beforeTearDown(self):
        clean = self.cleanup.get(self.db_name, None)
        if clean is not None:
            clean(self)


class SQLStorageTest(SQLStorageTestBase):

    def test_objectfield(self):
        dummy = self._dummy
        value = dummy.getAobjectfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        # Gadfly represents None as an empty string
        if self.db_name == 'Gadfly':
            self.failUnless(value == '')
        else:
            self.failUnless(value is None)
        dummy.setAobjectfield('Bla')
        value = dummy.getAobjectfield()
        __traceback_info__ = (self.db_name, repr(value), 'Bla')
        self.failUnless(value == 'Bla')

    def test_stringfield(self):
        dummy = self._dummy
        value = dummy.getAstringfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        # Gadfly represents None as an empty string
        if self.db_name == 'Gadfly':
            self.failUnless(value == '')
        else:
            self.failUnless(value is None)
        dummy.setAstringfield('Bla')
        value = dummy.getAstringfield()
        __traceback_info__ = (self.db_name, repr(value), 'Bla')
        self.failUnless(value == 'Bla')

    def test_stringfield_bug1003868(self):
        s = unicode('a?!', 'latin1')
        sp = self.portal.portal_properties.site_properties
        dummy = self._dummy

        sp.default_charset = 'latin1'
        dummy.setAstringfield(s)
        value = dummy.getAstringfield()
        __traceback_info__ = (self.db_name, repr(value), s)
        self.failUnlessEqual(value, s.encode(sp.default_charset))

        sp.default_charset = 'utf8'
        dummy.setAstringfield(s)
        value = dummy.getAstringfield()
        __traceback_info__ = (self.db_name, repr(value), s)
        self.failUnlessEqual(value, s.encode(sp.default_charset))

    def test_textfield(self):
        dummy = self._dummy
        value = dummy.getAtextfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        # Gadfly represents None as an empty string
        if self.db_name == 'Gadfly':
            self.failUnless(str(value) == '', (value, ''))
        else:
            self.failUnless(value is None, (value, None))
        dummy.setAtextfield('Bla')
        value = dummy.getAtextfield()
        __traceback_info__ = (self.db_name, repr(value), 'Bla')
        self.failUnless(str(value) == 'Bla', (value, 'Bla'))

    def test_datetimefield(self):
        dummy = self._dummy
        value = dummy.getAdatetimefield()
        __traceback_info__ = (self.db_name, repr(value), None)
        self.failUnless(value is None)
        now = DateTime()
        dummy.setAdatetimefield(now)
        value = dummy.getAdatetimefield()
        __traceback_info__ = (self.db_name, value, now)
        self.failUnless(value.Time() == now.Time())

    def test_linesfield(self):
        dummy = self._dummy
        value = dummy.getAlinesfield()
        __traceback_info__ = (self.db_name, repr(value), ())
        self.failUnless(value is ())
        dummy.setAlinesfield(('bla', 'blo'))
        value = dummy.getAlinesfield()
        __traceback_info__ = (self.db_name, repr(value), ('bla', 'blo'))
        self.failUnless(value == ('bla', 'blo'))

    def test_integerfield(self):
        dummy = self._dummy
        value = dummy.getAintegerfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        self.failUnless(value is None)
        dummy.setAintegerfield(23)
        value = dummy.getAintegerfield()
        __traceback_info__ = (self.db_name, repr(value), 23)
        self.failUnless(value == 23)

    def test_floatfield(self):
        dummy = self._dummy
        value = dummy.getAfloatfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        self.failUnless(value is None)
        dummy.setAfloatfield(12.34)
        value = dummy.getAfloatfield()
        __traceback_info__ = (self.db_name, repr(value), 12.34)
        self.failUnless(value == 12.34)

    def test_fixedpointfield(self):
        dummy = self._dummy
        value = dummy.getAfixedpointfield()
        __traceback_info__ = (self.db_name, repr(value), '0.00')
        self.failUnless(value == '0.00')
        dummy.setAfixedpointfield('2.3')
        value = dummy.getAfixedpointfield()
        __traceback_info__ = (self.db_name, repr(value), '2.3')
        self.failUnless(value == '2.30')

## Xiru: This test is done, but it is not testing the storage "in
## practice" because reference field is not SQLStorage aware.

##     def test_referencefield(self):
##         dummy = self._dummy
##         value = dummy.getAreferencefield()
##         __traceback_info__ = (self.db_name, repr(value), [])
##         self.failUnless(value == [])

##         portal = self.portal

##         # create another object instance (dummy2) and test the
##         # reference creation from dummy to dummy2
##         obj = Dummy(oid = 'dummy2')
##         portal._setObject('dummy2', obj)
##         obj = getattr(portal, 'dummy2')
##         dummy2 = obj

##         dummy.setAreferencefield([dummy2])
##         value = dummy.getAreferencefield()
##         __traceback_info__ = (self.db_name, repr(value), [dummy2])
##         self.failUnless(value == [dummy2])

##         # one more object instance (dummy3) and test the reference
##         # creation from dummy3 to dummy and dummy2
##         obj = Dummy(oid = 'dummy3')
##         portal._setObject('dummy3', obj)
##         obj = getattr(portal, 'dummy3')
##         dummy3 = obj

##         dummy3.setAreferencefield([dummy, dummy2])
##         value = dummy3.getAreferencefield()
##         __traceback_info__ = (self.db_name, repr(value), [dummy, dummy2])
##         self.failUnless(value == [dummy, dummy2])

    def test_booleanfield(self):
        dummy = self._dummy
        value = dummy.getAbooleanfield()
        __traceback_info__ = (self.db_name, repr(value), None)
        self.failUnless(not value)

        dummy.setAbooleanfield(1)
        value = dummy.getAbooleanfield()
        __traceback_info__ = (self.db_name, repr(value), 1)
        self.failUnless(value == 1)

        dummy.setAbooleanfield(0)
        value = dummy.getAbooleanfield()
        __traceback_info__ = (self.db_name, repr(value), 0)
        self.failUnless(value == 0)

    def test_rename(self):
        self.loginAsPortalOwner()
        dummy = self._dummy
        content = 'The book is on the table!'
        dummy.setAtextfield(content)
        got = dummy.getAtextfield()
        self.failUnless(str(got) == content, (got, content))
        portal = self.portal
        obj_id = 'dummy'
        new_id = 'new_dummy'
        # make sure we have _p_jar
        transaction.savepoint(optimistic=True)
        portal.manage_renameObject(obj_id, new_id)
        dummy = getattr(portal, new_id)
        got = dummy.getAtextfield()
        self.failUnless(str(got) == content, (got, content))

## Xiru: These 3 tests below need some refactory!

##         def test_parentUID(self):
##             portal = self.portal
##             makeContent(portal, portal_type='SimpleFolder', id='folder1')
##             folder1 = getattr(portal, 'folder1')
##             makeContent(portal, portal_type='SimpleFolder', id='folder2')
##             folder2 = getattr(portal, 'folder2')
##             obj_id = 'dummy'
##             # make sure we have _p_jar
##             transaction.savepoint(optimistic=True)
##             cb = portal.manage_cutObjects([obj_id])
##             folder1.manage_pasteObjects(cb)
##             # shit, why this does not work anymore?
##             doc = getattr(folder1, obj_id)
##             PUID1 = folder1.UID()
##             f = StringField('PARENTUID', storage=doc.Schema()['atextfield'].storage)
##             PUID = f.get(doc)
##             __traceback_info__ = (self.db_name, str(PUID), str(PUID1))
##             self.failUnless(PUID == PUID1)
##             # make sure we have _p_jar
##             transaction.savepoint(optimistic=True)
##             cb = folder1.manage_cutObjects([obj_id])
##             folder2.manage_pasteObjects(cb)
##             PUID2 = folder2.UID()
##             doc = getattr(folder2, obj_id)
##             PUID = f.get(doc)
##             __traceback_info__ = (self.db_name, str(PUID2), str(PUID))
##             self.failUnless(str(PUID2) == str(PUID))

##         def test_emptyPUID(self):
##             portal = self.portal
##             obj_id = 'dummy'
##             portal._setObject(obj_id, self._nwdummy)
##             doc = getattr(portal, obj_id)
##             doc.initializeArchetype()
##             f = StringField('PARENTUID',
##                             storage=doc.Schema()['atextfield'].storage)
##             PUID = f.get(doc)
##             __traceback_info__ = (self.db_name, str(PUID), 'None')
##             self.failUnless(PUID == 'None')

##         def test_nomoreparentUID(self):
##             portal = self.portal
##             makeContent(portal, portal_type='SimpleFolder', id='folder1')
##             folder1 = getattr(portal, 'folder1')
##             obj_id = 'dummy'
##             folder1._setObject(obj_id, self._nwdummy)
##             doc = getattr(folder1, obj_id)
##             doc.initializeArchetype()
##             PUID1 = folder1.UID()
##             f = StringField('PARENTUID',
##                             storage=doc.Schema()['atextfield'].storage)
##             PUID = f.get(doc)
##             __traceback_info__ = (self.db_name, str(PUID), str(PUID1))
##             self.failUnless(str(PUID) == str(PUID1))
##             # make sure we have _p_jar
##             transaction.savepoint(optimistic=True)
##             cb = folder1.manage_cutObjects(ids=(obj_id,))
##             portal.manage_pasteObjects(cb)
##             doc = getattr(portal, obj_id)
##             PUID = f.get(doc)
##             __traceback_info__ = (self.db_name, str(PUID), 'None')
##             self.failUnless(PUID == 'None')


# test each db

tests = []

for db_name in connectors.keys():

    class StorageTest(SQLStorageTest):
        db_name = db_name

    tests.append(StorageTest)


# run tests

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite
