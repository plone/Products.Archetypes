import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.public import *
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.config import PKG_NAME, USE_NEW_BASEUNIT

from test_classgen import Dummy, gen_dummy

from types import FunctionType

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

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ExtensibleMetadataTest))
        return suite
