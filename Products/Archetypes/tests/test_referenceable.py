import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_sitepolicy', 'Cannot import ArcheSiteTestCase')

from Acquisition import aq_base

from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.Archetypes.examples import *
from Products.Archetypes.config import *

class ReferenceableTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager( None, user )

    def test_hasUID( self ):
        site = self.getPortal()

        doc = makeContent( site
                           , portal_type='DDocument'
                           , title='Foo' )

        self.failUnless(hasattr(aq_base(doc), UUID_ATTR))
        self.failUnless(getattr(aq_base(doc), UUID_ATTR, None))


    def test_renamedontchangeUID( self ):
        site = self.getPortal()
        catalog = site.uid_catalog

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(site
                          , portal_type='DDocument'
                          , title='Foo'
                          , id=obj_id)

        UID = doc.UID()
        self.failUnless(catalog.uniqueValuesFor('UID') == (UID,))
        # ensure object has a _p_jar
        doc._p_jar = site._p_jar = self.app._p_jar
        new_oid = self.app._p_jar.new_oid
        doc._p_oid = new_oid()
        site.manage_renameObject(id=obj_id, new_id=new_id)
        doc = getattr(site, new_id)
        self.failUnless(catalog.uniqueValuesFor('UID') == (UID,))
        self.failUnless(doc.UID() == UID)

    def test_UIDclash( self ):
        site = self.getPortal()
        catalog = getattr(site, UID_CATALOG)

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent( site
                           , portal_type='DDocument'
                           , title='Foo'
                           , id=obj_id)

        UID = doc.UID()
        # ensure object has a _p_jar
        doc._p_jar = site._p_jar = self.app._p_jar
        new_oid = self.app._p_jar.new_oid
        doc._p_oid = new_oid()
        site.manage_renameObject(id=obj_id, new_id=new_id)

        #now, make a new one with the same ID and check it gets a different UID
        doc2 = makeContent( site
                            , portal_type='DDocument'
                            , title='Foo'
                            , id=obj_id)

        UID2 = doc2.UID()
        self.failIf(UID == UID2)
        uniq = catalog.uniqueValuesFor('UID')
        self.failUnless(UID in uniq)
        self.failUnless(UID2 in uniq)

    def test_relationships(self):
        site = self.getPortal()

        obj_id   = 'demodoc'
        known_id = 'known_doc'
        owned_id = 'owned_doc'

        a = makeContent( site, portal_type='DDocument',title='Foo', id=obj_id)
        b = makeContent( site, portal_type='DDocument',title='Foo', id=known_id)
        c = makeContent( site, portal_type='DDocument',title='Foo', id=owned_id)

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")
        a.addReference(c, "Owns")

        refs = a.getRefs()
        assert b in refs
        assert c in refs
        assert a.getRefs('Owns') == [c]
        assert c.getBRefs('Owns')== [a]
        rels = a.getRelationships()
        assert "KnowsAbout" in rels
        assert "Owns" in rels

        a.deleteReference(c, "Owns")
        assert a.getRefs() == [b]
        assert c.getBRefs() == []

    def test_back_relationships(self):
        site = self.getPortal()

        account_id = 'caixa'
        invoice_id = 'fatura'
        payment_id = 'entrada'
        future_payment_id = 'cta_receber'
        payment2_id = 'quitacao'

        account = makeContent( site, portal_type='DDocument',title='Account', id=account_id)
        invoice = makeContent( site, portal_type='DDocument',title='Invoice', id=invoice_id)
        payment = makeContent( site, portal_type='DDocument',title='Payment', id=payment_id)
        future_payment = makeContent( site, portal_type='DDocument',title='Future Payment', id=future_payment_id)
        payment2 = makeContent( site, portal_type='DDocument',title='Payment 2', id=payment2_id)

        invoice.addReference(payment, "Owns")
        invoice.addReference(future_payment, "Owns")
        future_payment.addReference(payment2, "Owns")
        payment.addReference(account, "From")
        payment2.addReference(account, "From")

        brels = account.getBRelationships()
        assert brels == ['From']
        brefs = account.getBRefs('From')
        assert brefs == [payment, payment2]

        brels = payment.getBRelationships()
        assert brels == ['Owns']
        brefs = payment.getBRefs('Owns')
        assert brefs == [invoice]

        brels = payment2.getBRelationships()
        assert brels == ['Owns']
        brefs = payment2.getBRefs('Owns')
        assert brefs == [future_payment]

        invoice.deleteReference(payment, "Owns")

        assert invoice.getRefs() == [future_payment]
        assert payment.getBRefs() == []

    def test_singleReference(self):
        # If an object is referenced don't record its reference again
        site = self.getPortal()
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
        site = self.getPortal()
        at = site.archetype_tool

        folder = makeContent( site, portal_type='SimpleFolder',
                              title='Foo', id='folder')
        nonRef = makeContent( folder, portal_type='Document',
                              title='Foo', id='nonRef')

        fuid = folder.UID()
        nuid = nonRef.UID()
        #We expect this to break, an aq_explicit would fix it but
        #we can't change the calling convention
        # XXX: but proxy index could
        #XXX: assert fuid != nuid

    def test_hasRelationship(self):
        site = self.getPortal()

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


    def test_folderishDeleteCleanup(self):
        site = self.getPortal()
        site.invokeFactory(type_name="Folder", id="reftest")
        folder = getattr(site, "reftest")

        a = makeContent(folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent(folder, portal_type='DDocument',title='Bar', id='b')
        a.addReference(b, "KnowsAbout")

        #again, lets assert the sanity of the UID and Ref Catalogs
        uc = site.uid_catalog
        rc = site.reference_catalog

        uids = uc.uniqueValuesFor('UID')
        assert a.UID() in uids
        assert b.UID() in uids

        refs = rc()
        assert len(refs) == 1
        ref = refs[0].getObject()
        assert ref.targetUID == b.UID()
        assert ref.sourceUID == a.UID()

        #Now Kill the folder and make sure it all went away
        site._delObject("reftest")
        self.verifyBrains()

        uids = uc.uniqueValuesFor('UID')
        #assert len(uids) == 0
        assert len(rc()) == 0

    def test_referenceReference(self):
        # Reference a reference object for fun (no, its like RDFs
        # metamodel)
        site = self.getPortal()
        rc = site.reference_catalog

        a = makeContent( site, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( site, portal_type='DDocument',title='Foo', id='b')
        c = makeContent( site, portal_type='DDocument',title='Foo', id='c')
        a.addReference(b)

        ref = a._getReferenceAnnotations().objectValues()[0]
        c.addReference(ref)
        ref.addReference(c)
        self.verifyBrains()

    def verifyBrains(self):
        site = self.getPortal()
        uc = getattr(site, UID_CATALOG)
        rc = getattr(site, REFERENCE_CATALOG)

        #Verify all UIDs resolve
        brains = uc()
        objects = [b.getObject() for b in brains]
        self.failIf(None in objects, """bad uid resolution""")

        #Verify all references resolve
        brains = rc()
        objects = [b.getObject() for b in brains]
        self.failIf(None in objects, """bad ref catalog resolution""")



    def beforeTearDown(self):
        noSecurityManager()
        ArcheSiteTestCase.beforeTearDown(self)


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ReferenceableTests))
        return suite
