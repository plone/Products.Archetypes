"""
Unittests for a Referenceable engine.

$Id: test_sitepolicy.py,v 1.5 2003/08/08 11:26:43 syt Exp $
"""

import unittest
# trigger zope imports
import test_classgen

from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.CMFPlone.Portal import manage_addSite
from Acquisition import aq_base
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl

def makeContent(site, portal_type, id='document', **kw ):
    site.invokeFactory( type_name=portal_type, id=id )
    content = getattr( site, id )

    return content

class SitePolicyTests( SecurityRequestTest ):

    def setUp(self):
        SecurityRequestTest.setUp(self)
        manage_addSite( self.root, 'testsite', \
                        custom_policy='Archetypes Site' )

    def test_new( self ):
        site = self.root.testsite
        # catalog should have one entry, for index_html or frontpage
        # and another for Members
        self.assertEqual( len( site.portal_catalog ), 2 )

    def test_availabledemotypes(self):
        site = self.root.testsite
        portal_types = [ x for x in site.portal_types.listContentTypes()]
        self.failUnless('DDocument' in portal_types)
        self.failUnless('SimpleType' in portal_types)
        self.failUnless('SimpleFolder' in portal_types)
        self.failUnless('ComplexType' in portal_types)
        self.failUnless('Fact' in portal_types)

    def test_creationdemotypes(self):
        site = self.root.testsite
        demo_types = ['DDocument', 'SimpleType', 'Fact', 'ComplexType']
        for t in demo_types:
            content = makeContent(site, portal_type=t, id=t)
            self.failUnless(t in site.contentIds())
            self.failUnless(not isinstance(content, DefaultDublinCoreImpl))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( SitePolicyTests ) )
    return suite

if __name__ == '__main__':
    unittest.main( defaultTest = 'test_suite' )
