import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_vocabulary', 'Cannot import ArcheSiteTestCase')

from StringIO import StringIO

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import listTypes
from Products.Archetypes.Schema import Schema
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.utils import DisplayList

schema = Schema((ReferenceField('test',
                                allowed_types='Test',
                                )))

class Dummy(BaseContent):
    schema = schema

    def Title(self):
        return self.getId()

    def _setObject(self, id, object):
        setattr(self, id, object)

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

    getPath = getURL

class DummyArchTool:

    def lookupObject(self, uid):
        return Dummy(uid)

    def deleteReferences(self, obj, reference):
        pass

class DummyCatalog:

    def __init__(self, brains=None):
        self._brains = brains or []

    def __call__(self, *args, **kwargs):
        return self._brains

    def getMetadataForUID(self, uid): # XXX stupid workaround, anyone?
        return {'UID': uid[1:]}

    indexes = lambda self:['portal_type']

    searchResults = __call__

sample_data = [('Test123', Dummy('Test123'), '/Test123'),
               ('Test124', None, '/Test124'),
               ('Test125', Dummy('Test125'), '/Test125')]


class VocabularyTest(ArcheSiteTestCase):

    def afterSetUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self.portal.dummy = Dummy(oid='dummy')
        self._dummy = self.portal.dummy
        # XXX doesn't work this way :(
        brains = [DummyBrain(*args) for args in sample_data]
        self._dummy.portal_catalog = DummyCatalog(brains)
        self._dummy.uid_catalog = DummyCatalog(brains)
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


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(VocabularyTest))
    return suite

if __name__ == '__main__':
    framework()
