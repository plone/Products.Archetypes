"""
Unittests for a Referenceable engine.

$Id: test_sitepolicy.py,v 1.5.4.3 2003/10/21 15:22:36 tiran Exp $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import * 

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_sitepolicy', 'Cannot import ArcheSiteTestCase')

import test_classgen

from Acquisition import aq_base
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
