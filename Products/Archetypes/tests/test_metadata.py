import os, sys
from types import FunctionType, ListType, TupleType
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.public import *
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.config import PKG_NAME, USE_NEW_BASEUNIT, \
     ZOPE_LINES_IS_TUPLE_TYPE
from DateTime import DateTime
from Acquisition import aq_base, aq_parent

from test_classgen import Dummy, gen_dummy, gen_class

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
    ('Identifier', '',                       ''),
    ('Language','setLanguage',               'language'),
    ('Rights','setRights',                   'rights'),

    # allowDiscussion is not part of the official DC metadata set
    ('allowDiscussion','isDiscussable','allowDiscussion'),
  ]

class DummyPortalMembership:
    def checkPermission(self, *args, **kwargs):
        return True

def addMetadataTo(obj, data='default', time=1000):
    """ """
    obj.setTitle(data)
    obj.setSubject([data])
    obj.setDescription(data)
    obj.setContributors([data])
    obj.setEffectiveDate(DateTime(time, 0))
    obj.setExpirationDate(DateTime(time, 0))
    obj.setFormat(data)
    obj.setLanguage(data)
    obj.setRights(data)

def compareMetadataOf(test, obj, data='default', time=1000):
    l_data = [data]
    if ZOPE_LINES_IS_TUPLE_TYPE:
        l_data = tuple(l_data)
    test.failUnless(obj.Title() == data, 'Title')
    test.failUnless(obj.Subject() == l_data,
                    'Subject: %s, %s' % (obj.Subject(), l_data))
    test.failUnless(obj.Description() == data, 'Description')
    test.failUnless(obj.Contributors() == l_data, 'Contributors')
    test.failUnless(obj.EffectiveDate() == DateTime(time, 0).ISO(),
                    'effective date')
    test.failUnless(obj.ExpirationDate() == DateTime(time, 0).ISO(),
                    'expiration date')
    # XXX BROKEN! test.failUnless(obj.Format() == data,
    #                             'Format: %s, %s' % (obj.Format(), data))
    test.failUnless(obj.Language() == data, 'Language')
    test.failUnless(obj.Rights() == data, 'Rights')


class DummyFolder(BaseFolder):

    portal_membership = DummyPortalMembership()

class ExtensibleMetadataTest( ArchetypesTestCase ):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        gen_dummy()
        self._dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        addMetadataTo(self._dummy)

    def beforeTearDown(self):
        del self._dummy
        ArchetypesTestCase.beforeTearDown(self)

    def testAccessors(self):
        obj = self._dummy
        for field in fieldList:
            accessor = field[0]
            fobj = getattr(obj, accessor, None)
            if not fobj:
                self.fail('Missing accessor for field: %s' % str(field))
            self.failUnless(hasattr(obj, accessor),
                            'Missing accessor %s' % accessor)
            self.failUnless((type(fobj) is FunctionType or
                             hasattr(fobj, '__call__')),
                            'Accessor %s is not callable' % accessor)

    def testMutators(self):
        obj = self._dummy
        for field in fieldList:
            mutator = field[1]
            if not mutator: continue
            fobj = getattr(obj, mutator, None)
            self.failUnless(hasattr(obj, mutator),
                            'Missing mutator %s' % mutator)
            self.failUnless((type(fobj) is FunctionType
                             or hasattr(fobj, '__call__')),
                            'Mutator %s is not callable' % mutator)

    def testMetaFields(self):
        obj = self._dummy
        for field in fieldList:
            meta = field[2]
            if not meta: continue
            md = aq_base(obj)._md
            field = aq_base(obj).Schema()[meta]
            self.failUnless(md.has_key(meta), 'Missing field %s' % meta)
            _marker = []
            value = md.get(meta, _marker)
            # We are checking here if the metadata
            # for a given field has been correctly initialized.
            self.failIf(value is _marker,
                        'Metadata field %s has not been correctly '
                        'initialized.' % meta)
            self.failUnless(field.isMetadata,
                            'isMetadata not set correctly for field %s.' % meta)

class ExtMetadataContextTest( ArchetypesTestCase ):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        gen_dummy()
        gen_class(DummyFolder)
        self._parent = DummyFolder(oid='parent')
        self._parent.initializeArchetype()
        # create dummy in context of a plone folder
        self._dummy = Dummy(oid='dummy').__of__(self._parent)
        self._dummy.initializeArchetype()

    def testContext(self):
        addMetadataTo(self._parent, data='parent', time=1001)
        addMetadataTo(self._dummy, data='dummy', time=9998)

        compareMetadataOf(self, self._parent, data='parent', time=1001)
        compareMetadataOf(self, self._dummy, data='dummy', time=9998)

    def testUnwrappedContext(self):
        addMetadataTo(self._parent, data='parent', time=1001)
        addMetadataTo(self._dummy, data='dummy', time=9998)

        compareMetadataOf(self, aq_base(self._parent), data='parent', time=1001)
        compareMetadataOf(self, aq_base(self._dummy), data='dummy', time=9998)

    def testIsParent(self):
        dummy_parent = aq_base(aq_parent(self._dummy))
        parent = aq_base(self._parent)
        self.failUnless(dummy_parent is parent,
                        ('Parent is not the parent of dummy! '
                         'Some tests will give you false results!'))

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
