import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Schema import Schemata, getNames
from Products.Archetypes import listTypes

from DateTime import DateTime
import unittest

schema = BaseSchema 

class Dummy(BaseContent):
    schema = schema
   
class SchemataTest( unittest.TestCase ):

    def setUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')

    def test_availschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        keys = schemata.keys()
        keys.sort()
        self.assertEqual(keys, ['default', 'metadata'])
        
    def test_nameschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        self.assertEqual(schemata['default'].getName(), 'default')
        self.assertEqual(schemata['metadata'].getName(), 'metadata')

    def test_baseschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        base_names = getNames(schemata['default'])
        self.assertEqual(base_names, ['id', 'title'])

    def test_metaschemata(self):
        dummy = self._dummy
        schemata = dummy.Schemata()
        meta_names = getNames(schemata['metadata'])
        self.assertEqual(meta_names, ['allowDiscussion', 'subject', 'description', \
                                      'contributors', 'effectiveDate', 'expirationDate', \
                                      'language', 'rights'])

    def tearDown( self ):
        del self._dummy
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SchemataTest),
        ))

if __name__ == '__main__':
    unittest.main()
