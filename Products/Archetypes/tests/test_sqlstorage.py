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
from Products.Archetypes.SQLStorage import GadflySQLStorage, MySQLStorage, OracleSQLStorage, PostgreSQLStorage

from DateTime import DateTime

from Products.ZGadflyDA.DA import Connection

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
   
class SQLStorageTest(unittest.TestCase):
    dummy_tool = None
    storage_class = None

    def setUp(self):
        gen_dummy(self.storage_class)
        self._dummy = dummy = Dummy(oid='dummy')
        self.dummy_tool.setup(dummy)
        dummy.initalizeArchetype()

    def test_textfield(self):
        dummy = self._dummy
        dummy.setAtextfield('Bla')
        text = dummy.getAtextfield()
        __traceback_info__ = repr(text)
        self.failUnless(str(text) == 'Bla')


#################################################################
# test Gadfly

class DummyToolGadfly:
    _connection_id = 'sql_connection'

    def __init__(self):
        self.connection = Connection(id=self._connection_id,
                                     title='connection',
                                     connection_string='demo', # default connection
                                     check=1, # connect immediatly
                                     )

    def getConnFor(self, instance=None):
        return self._connection_id

    def setup(self, instance):
        setattr(instance, TOOL_NAME, self)
        setattr(instance, self._connection_id, self.connection)

class GadflyStorageTest(SQLStorageTest):
    dummy_tool = DummyToolGadfly()
    storage_class = GadflySQLStorage

        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(GadflyStorageTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
