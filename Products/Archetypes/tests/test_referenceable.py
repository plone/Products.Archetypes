"""
Unittests for a Referenceable engine.

$Id: test_referenceable.py,v 1.8 2003/06/24 11:57:23 dreamcatcher Exp $
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
from Products.CMFPlone.Portal import manage_addSite

site = None

class ReferenceableTests( SecurityRequestTest ):
    def setUp(self):
        SecurityRequestTest.setUp(self)
        manage_addSite( self.root, 'testsite', \
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

    def test_relationships(self):
        site = self.root.testsite
        catalog = site.portal_catalog

        obj_id   = 'demodoc'
        known_id = 'known_doc'
        owned_id = 'owned_doc'

        a = makeContent( site, portal_type='DDocument',title='Foo', id=obj_id)
        b = makeContent( site, portal_type='DDocument',title='Foo', id=known_id)
        c = makeContent( site, portal_type='DDocument',title='Foo', id=owned_id)

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")
        a.addReference(c, "Owns")

        assert b in a.getRefs()
        assert c in a.getRefs()
        assert a.getRefs('Owns') == [c]
        assert c.getBRefs('Owns')== [a]
        rels = a.getRelationships()
        assert "KnowsAbout" in rels
        assert "Owns" in rels

        a.deleteReference(c)

        assert a.getRefs() == [b]
        assert c.getBRefs() == []


    def test_singleReference(self):
        # If an object is referenced don't record its reference again
        site = self.root.testsite
        catalog = site.portal_catalog
        at = site.archetype_tool

        a = makeContent( site, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( site, portal_type='DDocument',title='Foo', id='b')


        #Add the same ref twice
        a.addReference(b, "KnowsAbout")
        a.addReference(b, "KnowsAbout")

        assert len(a.getRefs('KnowsAbout')) == 1

        #In this case its a different relationship
        a.addReference(b, 'Flogs')
        assert len(a.getRefs('KnowsAbout')) == 1
        assert len(a.getRefs()) == 2


    def test_UIDunderContainment(self):
        # If an object is referenced don't record its reference again
        site = self.root.testsite
        catalog = site.portal_catalog
        at = site.archetype_tool

        folder = makeContent( site, portal_type='SimpleFolder',title='Foo', id='folder')
        nonRef = makeContent( folder, portal_type='DDocument',title='Foo', id='nonRef')

        ## This is really broken and I can't easily fix it
        assert folder.UID() == 'folder'
        assert nonRef.UID() != 'folder'

    def test_hasRelationship(self):
        site = self.root.testsite
        catalog = site.portal_catalog

        a = makeContent( site, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( site, portal_type='DDocument',title='Foo', id='b')
        c = makeContent( site, portal_type='DDocument',title='Foo', id='c')

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")

        assert a.hasRelationshipTo(b) == 1
        assert a.hasRelationshipTo(b, "KnowsAbout") == 1
        assert a.hasRelationshipTo(b, "Foo") == 0
        assert a.hasRelationshipTo(c) == 0
        assert a.hasRelationshipTo(c, "KnowsAbout") == 0

        #XXX HasRelationshipFrom  || ( 1 for ref 2 for bref?)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( ReferenceableTests ) )
    return suite

if __name__ == '__main__':
    unittest.main( defaultTest = 'test_suite' )
