""" 
Unittests for a Referenceable engine.

$Id: test_referenceable.py,v 1.2 2003/03/29 00:11:55 dreamcatcher Exp $
"""

import unittest
import Zope

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Acquisition import aq_base
from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.Archetypes.tests.test_sitepolicy import makeContent

class ReferenceableTests( SecurityRequestTest ):

    def setUp(self):
        SecurityRequestTest.setUp(self)
        self.root.manage_addProduct[ 'CMFPlone' ].manage_addSite( 'testsite', \
                                                                  custom_policy='Archetypes Site' )

    def test_hasUID( self ):

        site = self.root.testsite
        catalog = site.portal_catalog

        doc = makeContent( site
                           , portal_type='DDocument'
                           , title='Foo' )

        self.failUnless(hasattr(aq_base(doc), '_uid'))
        self.failUnless(getattr(aq_base(doc), '_uid', None))

    def test_renamedontchangeUID( self ):

        site = self.root.testsite
        catalog = site.portal_catalog

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent( site
                           , portal_type='DDocument'
                           , title='Foo'
                           , id=obj_id)

        UID = doc.UID()
        self.failUnless(catalog.uniqueValuesFor('UID') == (UID,))
        # ensure object has a _p_jar
        doc._p_jar = site._p_jar = self.root._p_jar
        new_oid = self.root._p_jar.new_oid
        site._p_oid = new_oid()
        doc._p_oid = new_oid()
        site.manage_renameObject(id=obj_id, new_id=new_id)
        doc = getattr(site, new_id)
        self.failUnless(catalog.uniqueValuesFor('UID') == (UID,))
        self.failUnless(doc.UID() == UID)

    def test_UIDclash( self ):

        site = self.root.testsite
        catalog = site.portal_catalog

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent( site
                           , portal_type='DDocument'
                           , title='Foo'
                           , id=obj_id)

        UID = doc.UID()
        # ensure object has a _p_jar
        doc._p_jar = site._p_jar = self.root._p_jar
        new_oid = self.root._p_jar.new_oid
        site._p_oid = new_oid()
        doc._p_oid = new_oid()
        site.manage_renameObject(id=obj_id, new_id=new_id)

        #now, make a new one with the same ID and check it gets a different UID
        doc2 = makeContent( site
                            , portal_type='DDocument'
                            , title='Foo'
                            , id=obj_id)
        
        UID2 = doc2.UID()
        self.failIf(UID == UID2)
        self.failUnless(catalog.uniqueValuesFor('UID') == (UID,UID2))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( ReferenceableTests ) )
    return suite

if __name__ == '__main__':
    unittest.main( defaultTest = 'test_suite' )
