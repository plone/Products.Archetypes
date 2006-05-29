import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Schema import Schemata, getNames
from Products.Archetypes import listTypes
from Products.Archetypes.VariableSchemaSupport import VariableSchemaSupport

from DateTime import DateTime
import unittest

schema = BaseSchema
schema1= BaseSchema + Schema(StringField('additionalField'),)

class Dummy(VariableSchemaSupport,BaseContent):
    schema = schema

class VarSchemataTest( ArchetypesTestCase ):

    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')

    def test_variableschema(self):

        dummy = self._dummy
        dummy.update(id='dummy1')
        self.assertEqual(dummy.getId(),'dummy1')

        #change the schema
        dummy.schema=schema1
        #try to read an old value using the new schema
        self.assertEqual(dummy.getId(),'dummy1')
        dummy.update(additionalField='flurb')
        #check if we can read the new field using the new schema
        self.assertEqual(dummy.getAdditionalField(),'flurb')

    def beforeTearDown(self):
        del self._dummy
        ArchetypesTestCase.beforeTearDown(self)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(VarSchemataTest))
        return suite
