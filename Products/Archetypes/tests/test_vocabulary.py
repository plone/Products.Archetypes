import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import listTypes
from Products.Archetypes.Schema import Schema
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.utils import DisplayList

import unittest

schema = Schema((ReferenceField('test',
                                allowed_types='Test',
                                )))

class Dummy(BaseContent):
    schema = schema

    def Title(self):
        return self.getId()

class DummyBrain:

    def __init__(self, UID='test', obj=None, path='/test'):
        self.UID = UID
        self.Title = UID
        self.obj = obj
        self.path = path

    def getObject(self):
        return self.obj

    def getURL(self):
        return self.path

class DummyCatalog:

    def __init__(self, brains=None):
        self._brains = brains or []

    def __call__(self, *args, **kwargs):
        return self._brains

    searchResults = __call__

class DummyArchTool:

    def lookupObject(self, uid):
        return Dummy(uid)

    def deleteReferences(self, obj, reference):
        pass

sample_data = [('Test123', Dummy('Test123'), '/Test123'),
               ('Test124', None, '/Test124'),
               ('Test125', Dummy('Test125'), '/Test125')]

class VocabularyTest( unittest.TestCase ):

    def setUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')
        brains = [DummyBrain(*args) for args in sample_data]
        self._dummy.portal_catalog = DummyCatalog(brains)
        self._dummy.archetype_tool = DummyArchTool()
        self._dummy.initializeArchetype()

    def test_vocabulary(self):
        dummy = self._dummy
        vocab = dummy.Schema()['test'].Vocabulary(dummy)
        expected = DisplayList([('', '<no reference>'),
                                ('Test123', 'Test123'),
                                ('Test124', 'Test124'),
                                ('Test125', 'Test125')])
        self.assertEqual(vocab, expected)

    def tearDown(self):
        del self._dummy

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(VocabularyTest),
        ))

if __name__ == '__main__':
    unittest.main()
