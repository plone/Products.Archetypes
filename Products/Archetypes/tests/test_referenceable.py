import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_sitepolicy', 'Cannot import ArcheSiteTestCase')

from Products.Archetypes.examples import *
from Products.Archetypes.config import *
from Products.Archetypes.utils import DisplayList

class ReferenceableTests(ArcheSiteTestCase):

    def verifyBrains(self):
        uc = getattr(self.portal, UID_CATALOG)
        rc = getattr(self.portal, REFERENCE_CATALOG)

        #Verify all UIDs resolve
        brains = uc()
        uobjects = [b.getObject() for b in brains]
        self.failIf(None in uobjects, """bad uid resolution""")

        #Verify all references resolve
        brains = rc()
        robjects = [b.getObject() for b in brains]
        self.failIf(None in robjects, """bad ref catalog resolution""")
        return uobjects, robjects

    def test_hasUID( self ):
        doc = makeContent( self.folder
                           , portal_type='DDocument'
                           , title='Foo' )

        self.failUnless(hasattr(aq_base(doc), UUID_ATTR))
        self.failUnless(getattr(aq_base(doc), UUID_ATTR, None))


    def test_renamedontchangeUID( self ):
        catalog = self.portal.uid_catalog

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(self.folder
                          , portal_type='DDocument'
                          , title='Foo'
                          , id=obj_id)


        UID = doc.UID()
        # This test made an assumption about other UIDs in the system
        # that are wrong with things like ATCT
        self.failUnless(UID in catalog.uniqueValuesFor('UID'))
        # ensure object has a _p_jar
        get_transaction().commit(1)
        self.folder.manage_renameObject(id=obj_id, new_id=new_id)
        doc = getattr(self.folder, new_id)
        self.failUnless(UID in catalog.uniqueValuesFor('UID'))
        self.failUnless(doc.UID() == UID)


    def test_renameKeepsReferences(self):
        container = makeContent(self.folder,
                                portal_type='SimpleFolder',
                                title='Spam',
                                id='container')

        obj1 = makeContent(self.folder.container,
                           portal_type='SimpleType',
                           title='Eggs',
                           id='obj1')
        obj2 = makeContent(self.folder.container,
                           portal_type='SimpleType',
                           title='Foo',
                           id='obj2')

        obj1.addReference(obj2)

        self.verifyBrains()
        get_transaction().commit(1)
        obj1.setId('foo')
        get_transaction().commit(1)

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])


    def test_renamecontainerKeepsReferences( self ):
        # test for #956677: renaming the container causes contained objects
        #                   to lose their refs
        container = makeContent(self.folder,
                                portal_type='SimpleFolder',
                                title='Spam',
                                id='container')
        obj1 = makeContent(self.folder.container,
                           portal_type='SimpleType',
                           title='Eggs',
                           id='obj1')
        obj2 = makeContent(self.folder,
                           portal_type='SimpleType',
                           title='Foo',
                           id='obj2')

        obj1.addReference(obj2)

        a,b = self.verifyBrains()
        get_transaction().commit(1)

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

        self.folder.manage_renameObject(id='container',
                                        new_id='cont4iner')
        c, d = self.verifyBrains()

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

    def test_UIDclash( self ):
        catalog = getattr(self.portal, UID_CATALOG)

        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent( self.folder
                           , portal_type='DDocument'
                           , title='Foo'
                           , id=obj_id)

        UID = doc.UID()
        # ensure object has a _p_jar
        get_transaction().commit(1)
        self.folder.manage_renameObject(id=obj_id, new_id=new_id)

        #now, make a new one with the same ID and check it gets a different UID
        doc2 = makeContent( self.folder
                            , portal_type='DDocument'
                            , title='Foo'
                            , id=obj_id)

        UID2 = doc2.UID()
        self.failIf(UID == UID2)
        uniq = catalog.uniqueValuesFor('UID')
        self.failUnless(UID in uniq)
        self.failUnless(UID2 in uniq)

    def test_relationships(self):

        obj_id   = 'demodoc'
        known_id = 'known_doc'
        owned_id = 'owned_doc'

        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id=obj_id)
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id=known_id)
        c = makeContent( self.folder, portal_type='DDocument',title='Foo', id=owned_id)

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

        account_id = 'caixa'
        invoice_id = 'fatura'
        payment_id = 'entrada'
        future_payment_id = 'cta_receber'
        payment2_id = 'quitacao'

        account = makeContent( self.folder, portal_type='DDocument',title='Account', id=account_id)
        invoice = makeContent( self.folder, portal_type='DDocument',title='Invoice', id=invoice_id)
        payment = makeContent( self.folder, portal_type='DDocument',title='Payment', id=payment_id)
        future_payment = makeContent( self.folder, portal_type='DDocument',title='Future Payment', id=future_payment_id)
        payment2 = makeContent( self.folder, portal_type='DDocument',title='Payment 2', id=payment2_id)

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
        at = self.portal.archetype_tool

        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id='b')

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
        at = self.portal.archetype_tool

        folder = makeContent( self.folder, portal_type='SimpleFolder',
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
        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id='b')
        c = makeContent( self.folder, portal_type='DDocument',title='Foo', id='c')

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")

        assert a.hasRelationshipTo(b) == 1
        assert a.hasRelationshipTo(b, "KnowsAbout") == 1
        assert a.hasRelationshipTo(b, "Foo") == 0
        assert a.hasRelationshipTo(c) == 0
        assert a.hasRelationshipTo(c, "KnowsAbout") == 0

        #XXX HasRelationshipFrom  || ( 1 for ref 2 for bref?)

    def test_folderishDeleteCleanup(self):
        self.folder.invokeFactory(type_name="Folder", id="reftest")
        folder = getattr(self.folder, "reftest")

        a = makeContent(folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent(folder, portal_type='DDocument',title='Bar', id='b')
        a.addReference(b, "KnowsAbout")

        #again, lets assert the sanity of the UID and Ref Catalogs
        uc = self.portal.uid_catalog
        rc = self.portal.reference_catalog

        uids = uc.uniqueValuesFor('UID')
        assert a.UID() in uids
        assert b.UID() in uids

        refs = rc()
        assert len(refs) == 1
        ref = refs[0].getObject()
        assert ref.targetUID == b.UID()
        assert ref.sourceUID == a.UID()

        #Now Kill the folder and make sure it all went away
        self.folder._delObject("reftest")
        self.verifyBrains()

        uids = uc.uniqueValuesFor('UID')
        #assert len(uids) == 0
        assert len(rc()) == 0

    def test_reindexUIDCatalog(self):
        catalog = self.portal.uid_catalog

        doc = makeContent(self.folder,
                          portal_type='DDocument',
                          id='demodoc')
        doc.update(title="sometitle")
        brain = catalog(UID=doc.UID())[0]
        self.assertEquals(brain.Title, doc.Title())

    def test_referenceReference(self):
        # Reference a reference object for fun (no, its like RDFs
        # metamodel)
        rc = self.portal.reference_catalog

        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id='b')
        c = makeContent( self.folder, portal_type='DDocument',title='Foo', id='c')
        a.addReference(b)

        ref = a._getReferenceAnnotations().objectValues()[0]
        c.addReference(ref)
        ref.addReference(c)
        self.verifyBrains()

    def test_referenceFieldVocab(self):
        dummy = makeContent(self.folder, portal_type="Refnode", id="dummy")
        test123 = makeContent(self.folder, portal_type="Refnode",
                              id="Test123")
        test124 = makeContent(self.folder, portal_type="Refnode",
                              id="Test124")
        test125 = makeContent(self.folder, portal_type="Refnode",
                              id="Test125")

        expected = DisplayList([
            (test123.UID(), test123.getId()),
            (test124.UID(), test124.getId()),
            (test125.UID(), test125.getId()),
            (dummy.UID(), dummy.getId()),
            ])
        assert dummy.Schema()['adds'].Vocabulary(dummy) == expected

        # We should have the option of nothing
        dummy.Schema()['adds'].required = 0
        dummy.Schema()['adds'].multiValued = 0

        expected = DisplayList([
            ('', '<no reference>'),
            (test123.UID(), test123.getId()),
            (test124.UID(), test124.getId()),
            (test125.UID(), test125.getId()),
            (dummy.UID(), dummy.getId()),
            ])
        assert dummy.Schema()['adds'].Vocabulary(dummy) == expected

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ReferenceableTests))
    return suite

if __name__ == '__main__':
    framework()
