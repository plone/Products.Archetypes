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

from DateTime import DateTime

# the id to use in the connection objects
connection_id = 'sql_connection'

# the db names and Connection objects
connectors = {}

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


class Dummy(BaseContent):
    pass

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

        #DateTimeField('adatetimefield',
        #              default = DateTime(),
        #              storage = storage_class(),
        #              widget = CalendarWidget(label = 'adatetimefield',
        #                                      description = 'Just a datetime field for the testing')),

        #LinesField('alinesfield',
        #           widget = StringWidget(label = 'alinesfield',
        #                                 description = 'Just a lines field for the testing')),

        IntegerField('aintegerfield',
                     default = 0,
                     storage = storage_class(),
                     widget = IntegerWidget(label = 'aintegerfield',
                                            description = 'Just a integer field for the testing')),

        FixedPointField('afixedpointfield',
                        default = '0',
                        storage = storage_class(),
                        widget = DecimalWidget(label = 'afixedwidthfield',
                                               description = 'Just a fixed-width field for the testing')),

        ReferenceField('areferencefield',
                       default = 0,
                       storage = storage_class(),
                       widget = ReferenceWidget(label = 'areferencefield',
                                                description = 'Just a reference field for the testing')),

        #BooleanField('abooleanfield',
        #             widget = StringWidget(label = 'abooleanfield',
        #                                   description = 'Just a boolean field for the testing')),

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
        self.connection = connectors[db_name]
        # to ensure test atomicity
        self.connection().tpc_abort()

    def getConnFor(self, instance=None):
        return connection_id

    def setup(self, instance):
        setattr(instance, TOOL_NAME, self)
        setattr(instance, connection_id, self.connection)

class SQLStorageTest(unittest.TestCase):
    db_name = ''

    def setUp(self):
        storage_class = getattr(SQLStorage, self.db_name + 'SQLStorage')
        gen_dummy(storage_class)
        self._dummy = dummy = Dummy(oid='dummy')
        dummy_tool = DummyTool(self.db_name)
        dummy_tool.setup(dummy)
        dummy.initalizeArchetype()

    def tearDown(self):
        db = getattr(self._dummy, connection_id)()
        db.tpc_abort()

    def test_objectfield(self):
        dummy = self._dummy
        dummy.setAobjectfield('Bla')
        value = dummy.getAobjectfield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')


    def test_textfield(self):
        dummy = self._dummy
        dummy.setAtextfield('Bla')
        value = dummy.getAtextfield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')

    def test_integerfield(self):
        dummy = self._dummy
        dummy.setAintegerfield(23)
        value = dummy.getAintegerfield()
        __traceback_info__ = repr(value)
        self.failUnless(value == 23)


    def test_fixedpointfield(self):
        dummy = self._dummy
        dummy.setAfixedpointfield('2.3')
        value = dummy.getAfixedpointfield()
        __traceback_info__ = repr(value)
        self.failUnless(value == '2.30')


    def test_referencefield(self):
        dummy = self._dummy
        dummy.setAreferencefield('Bla')
        value = dummy.getAreferencefield()
        __traceback_info__ = repr(value)
        self.failUnless(str(value) == 'Bla')



tests = []

#################################################################
# test each db

for db_name in connectors.keys():

    class StorageTestSubclass(SQLStorageTest):
        db_name = db_name

    tests.append(StorageTestSubclass)

#################################################################
# run tests
        
def test_suite():
    return unittest.TestSuite([unittest.makeSuite(test) for test in tests])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
