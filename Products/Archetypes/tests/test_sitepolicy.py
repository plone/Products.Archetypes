import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_sitepolicy', 'Cannot import ArcheSiteTestCase')

import test_classgen

from DateTime import DateTime
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl


class SitePolicyTests(ArcheSiteTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'Complex Type']

    def test_new( self ):
        # catalog should have one entry, for index_html or frontpage
        # and another for Members
        self.assertEqual( len( self.portal.portal_catalog ), 2 )

    def test_availabledemotypes(self):
        portal_types = self.portal.portal_types.listContentTypes()
        for t in self.demo_types:
            self.failUnless(t in portal_types,
                            "%s not available in portal_types." % t)

    def test_creationdemotypes(self):
        for t in self.demo_types:
            content = makeContent(self.folder, portal_type=t, id=t)
            self.failUnless(t in self.folder.contentIds())
            self.failUnless(not isinstance(content, DefaultDublinCoreImpl))

    # XXX Tests for some basic methods. Should be moved to
    # a separate test suite.
    def test_ComplexTypeGetSize(self):
        content = makeContent(self.folder, portal_type='Complex Type', id='ct')
        size = content.get_size()
        now = DateTime()
        content.setExpirationDate(now)
        new_size = size + len(str(now))
        self.assertEqual(new_size, content.get_size())
        content.setEffectiveDate(now)
        new_size = new_size + len(str(now))
        self.assertEqual(new_size, content.get_size())
        content.setIntegerfield(100)
        new_size = new_size + 2
        self.assertEqual(new_size, content.get_size())
        content.setIntegerfield(1)
        new_size = new_size - 2
        self.assertEqual(new_size, content.get_size())
        text = 'Bla bla bla'
        content.setTextfield(text)
        new_size = new_size + len(text)
        self.assertEqual(new_size, content.get_size())

    def test_SimpleFolderGetSize(self):
        content = makeContent(self.folder, portal_type='SimpleFolder', id='sf')
        size = content.get_size()
        now = DateTime()
        content.setExpirationDate(now)
        new_size = size + len(str(now))
        self.assertEqual(new_size, content.get_size())
        content.setEffectiveDate(now)
        new_size = new_size + len(str(now))
        self.assertEqual(new_size, content.get_size())
        text = 'Bla bla bla'
        content.setTitle(text)
        new_size = new_size + len(text)
        self.assertEqual(new_size, content.get_size())

    def test_addComplexTypeCtor(self):
        from Products.Archetypes.examples import ComplexType
        from Products.Archetypes.ClassGen import generateCtor
        addComplexType = generateCtor('ComplexType', ComplexType)
        id = addComplexType(self.folder, id='complex_type',
                            textfield='Bla', integerfield=1,
                            stringfield='A String')
        obj = getattr(self.folder, id)
        self.assertEqual(obj.getTextfield(), 'Bla')
        self.assertEqual(obj.getStringfield(), 'A String')
        self.assertEqual(obj.getIntegerfield(), 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SitePolicyTests))
    return suite

if __name__ == '__main__':
    framework()
