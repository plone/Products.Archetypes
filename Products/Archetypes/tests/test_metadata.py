import os, sys
from types import FunctionType, ListType, TupleType
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.public import *
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.config import PKG_NAME, USE_NEW_BASEUNIT
from Products.CMFPlone.PloneFolder import PloneFolder
from DateTime import DateTime

from test_classgen import Dummy, gen_dummy

fieldList = [
    # (accessor, mutator, field),
    ('Title', 'setTitle',                    ''),
    ('Creator', '',                          ''),
    ('Subject','setSubject',                 'subject'),
    ('Description','setDescription',         'description'),
    ('Publisher', '',                        ''),
    ('Contributors','setContributors',       'contributors'),
    ('Date', '',                             ''),
    ('CreationDate', '',                     ''),
    ('EffectiveDate','setEffectiveDate',     'effectiveDate'),
    ('ExpirationDate','setExpirationDate',   'expirationDate'),
    ('ModificationDate', '',                 ''),
    ('Type', '',                             ''),
    ('Format', 'setFormat',                  ''),
    ('Identifer', '',                        ''),
    ('Language','setLanguage',               'language'),
    ('Rights','setRights',                   'rights'),

    # allowDiscussion is not part of the official DC metadata set
    ('allowDiscussion','isDiscussable','allowDiscussion'),
  ]

class DummyPortalMembership:
    def checkPermission(self, *args, **kwargs):
        return True

class DummyPloneFolder(PloneFolder):
    portal_membership = DummyPortalMembership()
    def __init__(self, oid, **kwargs):
        PloneFolder.__init__(self, oid, **kwargs)

class ExtensibleMetadataTest( ArchetypesTestCase ):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        gen_dummy()
        self._dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

    def beforeTearDown(self):
        del self._dummy
        ArchetypesTestCase.beforeTearDown(self)

    def testAccessors(self):
        obj = self._dummy
        for field in fieldList:
            accessor = field[0]
            if not accessor: continue
            fobj = getattr(obj, accessor, None)
            self.failUnless(hasattr(obj, accessor), 'Missing accessor %s' % accessor)
            self.failUnless(type(fobj) is FunctionType or hasattr(fobj, '__call__'), 'Accessor %s is not callable' % accessor)

    def testMutators(self):
        obj = self._dummy
        for field in fieldList:
            mutator = field[1]
            if not mutator: continue
            fobj = getattr(obj, mutator, None)
            self.failUnless(hasattr(obj, mutator), 'Missing accesor %s' % mutator)
            self.failUnless(type(fobj) is FunctionType or hasattr(fobj, '__call__'), 'Mutator %s is not callable' % mutator)

    def testMetaFields(self):
        obj = self._dummy
        for field in fieldList:
            meta = field[2]
            if not meta: continue
            md = obj._md
            self.failUnless(md.has_key(meta), 'Missing field %s' % meta)
            fobj = md.get(meta, None)
            # XXX
            # that's strange. I was pretty shure that the type is always a ObjectField based instance
            if fobj and fobj != 'en':
                self.failUnless(IObjectField.isImplementedBy(fobj), 'Meta field %s class is not a subclass of ObjectField: %s (type: %s)' % (meta, fobj, type(fobj)))
                self.failUnless(fobj.isMetadata, 'isMetadata != 1 for field %s.' % meta)


class ExtMetadataContextTest( ArchetypesTestCase ):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        gen_dummy()
        self._parent = DummyPloneFolder(oid='parent')
        # create dummy in context of a plone folder
        self._dummy = Dummy(oid='dummy').__of__(self._parent)
        self._dummy.initializeArchetype()

    def addMetadataTo(self, obj, data='default', time=1000):
        """
        """
        obj.setTitle(data)
        obj.setSubject(tuple(data))
        obj.setDescription(data)
        obj.setContributors(tuple(data,))
        obj.setEffectiveDate(DateTime(time, 0))
        obj.setExpirationDate(DateTime(time, 0))
        obj.setFormat(data)
        obj.setLanguage(tuple(data))
        obj.setRights(data)
        
    def compareMetadataOf(self, obj, data='default', time=1000):
        self.failUnless(obj.Title() == data, 'Title')
        self.failUnless(obj.Subject() == tuple(data), 'Subject: %s, %s' % (obj.Subject(), tuple(data)))
        self.failUnless(obj.Description() == data, 'Description')
        self.failUnless(obj.Contributors() == tuple(data), 'Contributors')
        self.failUnless(obj.EffectiveDate() == DateTime(time, 0).ISO(), 'effective date')
        self.failUnless(obj.ExpirationDate() == DateTime(time, 0).ISO(), 'expiration date')
        # XXX BROKEN! self.failUnless(obj.Format() == data, 'Format: %s, %s' % (obj.Format(), data))
        self.failUnless(obj.Language() == tuple(data), 'Language')
        self.failUnless(obj.Rights() == data, 'Rights')

    def testContext(self):
        self.addMetadataTo(self._parent, data='parent', time=1001)
        self.addMetadataTo(self._dummy, data='dummy', time=9998)
        
        self.compareMetadataOf(self._parent, data='parent', time=1001)
        self.compareMetadataOf(self._dummy, data='dummy', time=9998)

    def beforeTearDown(self):
        del self._dummy
        del self._parent
        ArchetypesTestCase.beforeTearDown(self)


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ExtensibleMetadataTest))
        suite.addTest(unittest.makeSuite(ExtMetadataContextTest))
        return suite
