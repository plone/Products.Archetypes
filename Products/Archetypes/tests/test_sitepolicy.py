import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_sitepolicy', 'Cannot import ArcheSiteTestCase')

import test_classgen

from Acquisition import aq_base
from DateTime import DateTime
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl

def makeContent(site, portal_type, id='document', **kw ):
    site.invokeFactory( type_name=portal_type, id=id )
    content = getattr( site, id )

    return content

class SitePolicyTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager( None, user )

    def test_new( self ):
        site = self.getPortal()
        # catalog should have one entry, for index_html or frontpage
        # and another for Members
        self.assertEqual( len( site.portal_catalog ), 2 )

    def test_availabledemotypes(self):
        site = self.getPortal()
        portal_types = [ x for x in site.portal_types.listContentTypes()]
        self.failUnless('DDocument' in portal_types)
        self.failUnless('SimpleType' in portal_types)
        self.failUnless('SimpleFolder' in portal_types)
        self.failUnless('ComplexType' in portal_types)
        self.failUnless('Fact' in portal_types)

    def test_creationdemotypes(self):
        site = self.getPortal()
        demo_types = ['DDocument', 'SimpleType', 'Fact', 'ComplexType']
        for t in demo_types:
            content = makeContent(site, portal_type=t, id=t)
            self.failUnless(t in site.contentIds())
            self.failUnless(not isinstance(content, DefaultDublinCoreImpl))

    # XXX Tests for some basic methods. Should be moved to
    # a separate test suite.
    def test_ComplexTypegetSize(self):
        site = self.getPortal()
        content = makeContent(site, portal_type='ComplexType', id='ct')
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

    def test_SimpleFoldergetSize(self):
        site = self.getPortal()
        content = makeContent(site, portal_type='SimpleFolder', id='sf')
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
        site = self.getPortal()
        id = addComplexType(site, id='complex_type',
                            textfield='Bla', integerfield=1,
                            stringfield='A String')
        obj = getattr(site, id)
        self.assertEqual(obj.getTextfield(), 'Bla')
        self.assertEqual(obj.getStringfield(), 'A String')
        self.assertEqual(obj.getIntegerfield(), 1)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(SitePolicyTests))
        return suite
