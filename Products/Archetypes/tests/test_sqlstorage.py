import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

import unittest
from zExceptions.ExceptionFormatter import format_exception
# print __traceback_info__, etc
def pretty_exc(self, exc):
    t, e, tb = exc
    return ''.join(format_exception(t, e, tb, format_src=1))
unittest.TestResult._exc_info_to_string = pretty_exc

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME, TOOL_NAME
from Products.Archetypes import listTypes
from Products.Archetypes import SQLStorage
from Products.Archetypes.SQLMethod import SQLMethod
from Products.Archetypes.tests.test_rename import RenameTests
from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.CMFCore.TypesTool import FactoryTypeInformation

from DateTime import DateTime

# the id to use in the connection objects
connection_id = 'sql_connection'

# the db names and Connection objects
connectors = {}
cleanup = {}

try:
  # gadfly storage is currently b0rked, we don't want to test it yet
  if 0:
    from Products.ZGadflyDA.DA import Connection
    connectors['Gadfly'] = Connection(id=connection_id,
                                      title='connection',
                                      connection_string='demo', # default connection
                                      check=1, # connect immediatly
                                      )
except ImportError:
    pass


try:
    from Products.ZPsycopgDA.DA import Connection
    connectors['Postgre'] = Connection(id=connection_id,
                                       title='connection',
                                       connection_string='dbname=demo user=demo',
                                       zdatetime=1, # use Zope's DateTime, not mxDateTime
                                       check=1, # connect immediatly
                                       )
except ImportError:
    pass

try:
    import _mysql
    from _mysql_exceptions import OperationalError, NotSupportedError
    from Products.ZMySQLDA.DA import Connection
    # XXX we need to figure out why the MySQL tests with transactional
    # are failing.
    transactional = 0
    if transactional:
            connectors['MySQL'] = Connection(id=connection_id,
                                             title='connection',
                                             connection_string='+demo@localhost demo demo',
                                             check=1, # connect immediatly
                                             )
    if not transactional:
        connectors['MySQL'] = Connection(id=connection_id,
                                         title='connection',
                                         connection_string='-demo@localhost demo demo',
                                         check=1, # connect immediatly
                                         )
        def cleanupMySQL(self):
            instance = self._dummy
            args = {}
            args['table'] = 'Dummy'
            storage = self._storage_class
            method = SQLMethod(instance)
            method.edit(connection_id, ' '.join(args.keys()), storage.query_drop)
            query, result = method(test__=1, **args)

        cleanup['MySQL'] = cleanupMySQL

except ImportError:
    pass


class Dummy(BaseContent):
    """ A dummy content object for testing """
    _uid = 'Dummy.2002-01-01.2302'


default_time = DateTime()

def gen_dummy(storage_class):
    Dummy.schema = Schema((
        ObjectField('aobjectfield',
                    storage = storage_class(),
                    widget = StringWidget(label = 'aobjectfield',
                                          description = 'Just a object field for the testing')),

        TextField('atextfield',
                  storage = storage_class(),
                  widget = StringWidget(label = 'atextfield',
                                        description = 'Just a text field for the testing')),

        DateTimeField('adatetimefield',
                      default = default_time,
                      storage = storage_class(),
                      widget = CalendarWidget(label = 'adatetimefield',
                                              description = 'Just a datetime field for the testing')),

        #LinesField('alinesfield',
        #           widget = StringWidget(label = 'alinesfield',
        #                                 description = 'Just a lines field for the testing')),

        IntegerField('aintegerfield',
                     default = 0,
                     storage = storage_class(),
                     widget = IntegerWidget(label = 'aintegerfield',
                                            description = 'Just a integer field for the testing')),

        FixedPointField('afixedpointfield',
                        default = '0.0',
                        storage = storage_class(),
                        widget = DecimalWidget(label = 'afixedwidthfield',
                                               description = 'Just a fixed-width field for the testing')),

        ReferenceField('areferencefield',
                       storage = storage_class(),
                       widget = ReferenceWidget(label = 'areferencefield',
                                                description = 'Just a reference field for the testing')),

        BooleanField('abooleanfield',
                     widget = StringWidget(label = 'abooleanfield',
                                           description = 'Just a boolean field for the testing')),

        #ImageField('aimagefield',
        #           original_size = (600,600),
        #           sizes = {'mini' : (80,80),
        #                    'normal' : (200,200),
        #                    'big' : (300,300),
        #                    'maxi' : (500,500)},
        #           widget = ImageWidget(label = 'aimagefield',
        #                                description = 'Just a image field for the testing'))
    ))
    registerType(Dummy)
    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)

class DummyTool:
    def __init__(self, db_name):
        self.sql_connection = connectors[db_name]
        # to ensure test atomicity
        # XXX Need a way to make this work with MySQL when non-transactional
        # self.sql_connection().tpc_abort()

    def getConnFor(self, instance=None):
        return connection_id

    def setup(self, instance):
        setattr(instance, TOOL_NAME, self)
        setattr(instance, connection_id, self.sql_connection)

class SQLStorageTest(unittest.TestCase):
    # abstract base class for the tests
    db_name = ''

    def setUp(self):
        storage_class = getattr(SQLStorage, self.db_name + 'SQLStorage')
        gen_dummy(storage_class)
        self._storage_class = storage_class
        self._dummy = dummy = Dummy(oid='dummy')
        dummy_tool = DummyTool(self.db_name)
        dummy_tool.setup(dummy)
        dummy.initializeArchetype()

    def tearDown(self):
        db = getattr(self._dummy, connection_id)()
        db.tpc_abort()

    def test_objectfield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAobjectfield() == None)
        dummy.setAobjectfield('Bla')
        value = dummy.getAobjectfield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')

    def test_textfield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAtextfield() == '')
        dummy.setAtextfield('Bla')
        value = dummy.getAtextfield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')

    def test_datetimefield(self):
        dummy = self._dummy
        default = dummy.getAdatetimefield()
        self.failUnless(default.Time() == default_time.Time())
        now = DateTime()
        dummy.setAdatetimefield(now)
        value = dummy.getAdatetimefield()
        __traceback_info__ = (value, now)
        # Precision in seconds is enough for us.
        # Also, MySQL doesnt stores milliseconds AFAIK
        self.failUnless(value.Time() == now.Time())

    def test_integerfield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAintegerfield() == 0)
        dummy.setAintegerfield(23)
        value = dummy.getAintegerfield()
        __traceback_info__ = repr(value)
        self.failUnless(value == 23)

    def test_fixedpointfield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAfixedpointfield() == '0.00')
        dummy.setAfixedpointfield('2.3')
        value = dummy.getAfixedpointfield()
        __traceback_info__ = repr(value)
        self.failUnless(value == '2.30')

    def test_referencefield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAreferencefield() is None)
        dummy.setAreferencefield('Bla')
        value = dummy.getAreferencefield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')

    def test_booleanfield(self):
        dummy = self._dummy
        self.failUnless(dummy.getAbooleanfield() is None)
        dummy.setAbooleanfield(1)
        value = dummy.getAbooleanfield()
        __traceback_info__ = repr(value)
        self.failUnless(value == 1)

tests = []

#################################################################
# test each db

for db_name in connectors.keys():

    class StorageTestSubclass(SQLStorageTest):
        db_name = db_name
        cleanup = cleanup

        def tearDown(self):
            clean = self.cleanup.get(self.db_name, None)
            if clean is None:
                SQLStorageTest.tearDown(self)

    tests.append(StorageTestSubclass)


#################################################################
# test rename with each db
for db_name in connectors.keys():

    class StorageTestRenameSubclass(RenameTests):

        db_name = db_name
        cleanup = cleanup

        def setUp(self):
            RenameTests.setUp(self)
            site = self.root.testsite
            storage_class = getattr(SQLStorage, self.db_name + 'SQLStorage')
            gen_dummy(storage_class)
            self._storage_class = storage_class
            self._nwdummy = dummy = Dummy(oid='dummy')
            self._dummy = dummy.__of__(site)
            dummy_tool = DummyTool(self.db_name)
            dummy_tool.setup(site)
            typesTool = site.portal_types
            typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                                id='Dummy',
                                                typeinfo_name='CMFDefault: Document')
            dummy.__factory_meta_type__ = 'ArchExample Content'

        def test_rename(self):
            site = self.root.testsite
            obj_id = 'dummy'
            new_id = 'new_demodoc'
            site._setObject(obj_id, self._nwdummy)
            doc = getattr(site, obj_id)
            doc.initializeArchetype()
            content = 'The book is on the table!'
            doc.setAtextfield(content)
            self.failUnless(str(doc.getAtextfield()) == content)
            #make sure we have _p_jar
            doc._p_jar = site._p_jar = self.root._p_jar
            new_oid = self.root._p_jar.new_oid
            site._p_oid = new_oid()
            doc._p_oid = new_oid()
            site.manage_renameObject(obj_id, new_id)
            doc = getattr(site, new_id)
            self.failUnless(str(doc.getAtextfield()) == content)

        def test_parentUID(self):
            site = self.root.testsite
            makeContent(site, portal_type='SimpleFolder', id='folder1')
            folder1 = getattr(site, 'folder1')
            makeContent(site, portal_type='SimpleFolder', id='folder2')
            folder2 = getattr(site, 'folder2')
            obj_id = 'dummy'
            folder1._setObject(obj_id, self._nwdummy)
            doc = getattr(folder1, obj_id)
            doc.initializeArchetype()
            PUID1 = folder1.UID()
            f = ObjectField('PARENTUID', storage=doc.Schema()['atextfield'].storage)
            PUID = f.get(doc)
            self.failUnless(str(PUID) == str(PUID1))
            #make sure we have _p_jar
            doc._p_jar = folder1._p_jar = site._p_jar = self.root._p_jar
            new_oid = self.root._p_jar.new_oid
            site._p_oid = new_oid()
            folder1._p_oid = new_oid()
            doc._p_oid = new_oid()
            cb = folder1.manage_cutObjects(ids=(obj_id,))
            folder2.manage_pasteObjects(cb)
            PUID2 = folder2.UID()
            doc = getattr(folder2, obj_id)
            PUID = f.get(doc)
            self.failUnless(str(PUID2) == str(PUID))

        def test_emptyPUID(self):
            site = self.root.testsite
            obj_id = 'dummy'
            site._setObject(obj_id, self._nwdummy)
            doc = getattr(site, obj_id)
            doc.initializeArchetype()
            f = ObjectField('PARENTUID', storage=doc.Schema()['atextfield'].storage)
            PUID = f.get(doc)
            self.failUnless(PUID is None)

        def test_nomoreparentUID(self):
            site = self.root.testsite
            makeContent(site, portal_type='SimpleFolder', id='folder1')
            folder1 = getattr(site, 'folder1')
            obj_id = 'dummy'
            folder1._setObject(obj_id, self._nwdummy)
            doc = getattr(folder1, obj_id)
            doc.initializeArchetype()
            PUID1 = folder1.UID()
            f = ObjectField('PARENTUID', storage=doc.Schema()['atextfield'].storage)
            PUID = f.get(doc)
            self.failUnless(str(PUID) == str(PUID1))
            #make sure we have _p_jar
            doc._p_jar = folder1._p_jar = site._p_jar = self.root._p_jar
            new_oid = self.root._p_jar.new_oid
            site._p_oid = new_oid()
            folder1._p_oid = new_oid()
            doc._p_oid = new_oid()
            cb = folder1.manage_cutObjects(ids=(obj_id,))
            site.manage_pasteObjects(cb)
            doc = getattr(site, obj_id)
            PUID = f.get(doc)
            self.failUnless(PUID is None)

        def tearDown(self):
            cleanup = self.cleanup.get(self.db_name, None)
            if cleanup is None:
                db = getattr(self._dummy, connection_id)()
                db.tpc_abort()
            else:
                cleanup(self)
            RenameTests.tearDown(self)

    tests.append(StorageTestRenameSubclass)

#################################################################
# run tests

def test_suite():
    return unittest.TestSuite([unittest.makeSuite(test) for test in tests])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
