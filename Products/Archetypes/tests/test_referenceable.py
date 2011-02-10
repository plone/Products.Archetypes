################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

from Acquisition import aq_base
import transaction

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.Archetypes.examples import *
from Products.Archetypes.config import *
from Products.Archetypes.atapi import DisplayList
from plone.uuid.interfaces import IUUIDAware, IUUID

class BaseReferenceableTests(ATSiteTestCase):

    FOLDER_TYPE = None

    def verifyBrains(self):
        uc = getattr(self.portal, UID_CATALOG)
        rc = getattr(self.portal, REFERENCE_CATALOG)

        #Verify all UIDs resolve
        uids = uc.uniqueValuesFor('UID')
        brains = uc(dict(UID=uids))

        uobjects = [b.getObject() for b in brains]
        self.failIf(None in uobjects, """bad uid resolution""")

        #Verify all references resolve
        uids = rc.uniqueValuesFor('UID')
        brains = rc(dict(UID=uids))

        robjects = [b.getObject() for b in brains]
        self.failIf(None in robjects, """bad ref catalog resolution""")
        return uobjects, robjects

    def test_hasUID( self ):
        doc = makeContent( self.folder
                           , portal_type='DDocument'
                           , title='Foo' )

        self.failUnless(hasattr(aq_base(doc), UUID_ATTR))
        self.failUnless(getattr(aq_base(doc), UUID_ATTR, None))

    def test_uuid(self):
        doc = makeContent( self.folder
                           , portal_type='DDocument'
                           , title='Foo' )

        self.failUnless(IUUIDAware.providedBy(doc))
        uuid = IUUID(doc, None)
        self.failUnless(uuid == doc.UID())

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
        transaction.savepoint(optimistic=True)
        self.folder.manage_renameObject(id=obj_id, new_id=new_id)
        doc = getattr(self.folder, new_id)
        self.failUnless(UID in catalog.uniqueValuesFor('UID'))
        self.assertEquals(doc.UID(), UID)


    def test_renameKeepsReferences(self):
        container = makeContent(self.folder,
                                portal_type=self.FOLDER_TYPE,
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
        transaction.savepoint(optimistic=True)
        obj1.setId('foo')
        transaction.savepoint(optimistic=True)

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

        self.verifyBrains()
        transaction.savepoint(optimistic=True)
        obj2.setId('bar')
        transaction.savepoint(optimistic=True)

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

        self.verifyBrains()

    def test_renamecontainerKeepsReferences( self ):
        # test for #956677: renaming the container causes contained objects
        #                   to lose their refs
        container = makeContent(self.folder,
                                portal_type=self.FOLDER_TYPE,
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
        transaction.savepoint(optimistic=True)

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

        self.folder.manage_renameObject(id='container',
                                        new_id='cont4iner')
        c, d = self.verifyBrains()

        obj1 = self.folder.cont4iner.obj1
        obj2 = self.folder.cont4iner.obj2

        self.assertEquals(obj2.getBRefs(), [obj1])
        self.assertEquals(obj1.getRefs(), [obj2])

    def test_renamecontainerKeepsReferences2( self ):
        # test for [ 1013363 ] References break on folder rename
        folderA = makeContent(self.folder,
                                portal_type=self.FOLDER_TYPE,
                                title='Spam',
                                id='folderA')
        objA = makeContent(self.folder.folderA,
                           portal_type='SimpleType',
                           title='Eggs',
                           id='objA')

        folderB = makeContent(self.folder,
                                portal_type=self.FOLDER_TYPE,
                                title='Spam',
                                id='folderB')
        objB = makeContent(self.folder.folderB,
                           portal_type='SimpleType',
                           title='Eggs',
                           id='objB')

        objA.addReference(objB)

        a, b = self.verifyBrains()
        transaction.savepoint(optimistic=True)

        self.assertEquals(objB.getBRefs(), [objA])
        self.assertEquals(objA.getRefs(), [objB])

        # now rename folder B and see if objA still points to objB
        self.folder.manage_renameObject(id='folderB',
                                        new_id='folderC')
        c, d = self.verifyBrains()

        objB = self.folder.folderC.objB

        # check references
        self.assertEquals(objB.getBRefs(), [objA])
        self.assertEquals(objA.getRefs(), [objB])

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
        transaction.savepoint(optimistic=True)
        self.folder.manage_renameObject(id=obj_id, new_id=new_id)

        #now, make a new one with the same ID and check it gets a different UID
        doc2 = makeContent( self.folder
                            , portal_type='DDocument'
                            , title='Foo'
                            , id=obj_id)

        UID2 = doc2.UID()
        self.failIf(UID == UID2)
        uniq = catalog.uniqueValuesFor('UID')
        self.failUnless(UID in uniq, (UID, uniq))
        self.failUnless(UID2 in uniq, (UID, uniq))

    def test_setUID_keeps_relationships(self):
        obj_id   = 'demodoc'
        known_id = 'known_doc'
        owned_id = 'owned_doc'

        a = makeContent(self.folder, portal_type='DDocument',
                        title='Foo', id=obj_id)
        b = makeContent(self.folder, portal_type='DDocument',
                        title='Foo', id=known_id)
        c = makeContent(self.folder, portal_type='DDocument',
                        title='Foo', id=owned_id)

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")
        b.addReference(a, "KnowsAbout")
        a.addReference(c, "Owns")

        refs = a.getRefs()
        self.failUnless(b in refs, (b, refs))
        self.failUnless(c in refs, (c, refs))
        self.assertEquals(a.getRefs('KnowsAbout'), [b])
        self.assertEquals(b.getRefs('KnowsAbout'), [a])
        self.assertEquals(a.getRefs('Owns'), [c])
        self.assertEquals(c.getBRefs('Owns'), [a])

        old_uid = a.UID()

        # Check existing forward refs
        fw_refs = a.getReferenceImpl()
        old_refs = []
        [old_refs.append(o.sourceUID) for o in fw_refs
         if not o.sourceUID in old_refs]
        self.assertEquals(len(old_refs), 1)
        self.assertEquals(old_refs[0], old_uid)

        # Check existing backward refs
        fw_refs = a.getBackReferenceImpl()
        old_refs = []
        [old_refs.append(o.targetUID) for o in fw_refs
         if not o.targetUID in old_refs]
        self.assertEquals(len(old_refs), 1)
        self.assertEquals(old_refs[0], old_uid)

        new_uid = '9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9x9'
        a._setUID(new_uid)
        self.assertEquals(a.UID(), new_uid)

        # Check existing forward refs got reassigned
        fw_refs = a.getReferenceImpl()
        new_refs = []
        [new_refs.append(o.sourceUID) for o in fw_refs
         if not o.sourceUID in new_refs]
        self.assertEquals(len(new_refs), 1)
        self.assertEquals(new_refs[0], new_uid)

        # Check existing backward refs got reassigned
        fw_refs = a.getBackReferenceImpl()
        new_refs = []
        [new_refs.append(o.targetUID) for o in fw_refs
         if not o.targetUID in new_refs]
        self.assertEquals(len(new_refs), 1)
        self.assertEquals(new_refs[0], new_uid)

        refs = a.getRefs()
        self.failUnless(b in refs, (b, refs))
        self.failUnless(c in refs, (c, refs))
        self.assertEquals(a.getRefs('KnowsAbout'), [b])
        self.assertEquals(b.getRefs('KnowsAbout'), [a])
        self.assertEquals(a.getRefs('Owns'), [c])
        self.assertEquals(c.getBRefs('Owns'), [a])

        self.verifyBrains()

    def test_relationships(self):

        obj_id   = 'demodoc'
        known_id = 'known_doc'
        owned_id = 'owned_doc'
        other_id = 'other_doc'

        a = makeContent( self.folder, portal_type='DDocument',
                         title='Foo', id=obj_id)
        b = makeContent( self.folder, portal_type='DDocument',
                         title='Foo', id=known_id)
        c = makeContent( self.folder, portal_type='DDocument',
                         title='Foo', id=owned_id)

        #Two made up kinda refs
        a.addReference(b, "KnowsAbout")
        a.addReference(c, "Owns")

        refs = a.getRefs()
        self.failUnless(b in refs, (b, refs))
        self.failUnless(c in refs, (c, refs))
        self.assertEquals(a.getRefs('Owns'), [c])
        self.assertEquals(c.getBRefs('Owns'), [a])
        rels = a.getRelationships()
        self.failUnless("KnowsAbout" in rels, ("KnowsAbout", rels))
        self.failUnless("Owns" in rels, ("Owns", rels))

        a.deleteReference(c, "Owns")
        self.assertEquals(a.getRefs(), [b])
        self.assertEquals(c.getBRefs(), [])

        #test querying references using the targetObject parameter
        d = makeContent( self.folder, portal_type='DDocument',
                         title='Foo', id=other_id)

        a.addReference(d,'Owns')
        a.addReference(d,'KnowsAbout')

        self.assertEqual(len(a.getReferenceImpl()),3)
        #get only refs to d
        self.assertEqual(len(a.getReferenceImpl(targetObject=d)),2)

    def test_back_relationships(self):

        account_id = 'caixa'
        invoice_id = 'fatura'
        payment_id = 'entrada'
        future_payment_id = 'cta_receber'
        payment2_id = 'quitacao'

        account = makeContent( self.folder, portal_type='DDocument',
                               title='Account', id=account_id)
        invoice = makeContent( self.folder, portal_type='DDocument',
                               title='Invoice', id=invoice_id)
        payment = makeContent( self.folder, portal_type='DDocument',
                               title='Payment', id=payment_id)
        future_payment = makeContent( self.folder, portal_type='DDocument',
                                      title='Future Payment',
                                      id=future_payment_id)
        payment2 = makeContent( self.folder, portal_type='DDocument',
                                title='Payment 2', id=payment2_id)

        invoice.addReference(payment, "Owns")
        invoice.addReference(future_payment, "Owns")
        future_payment.addReference(payment2, "Owns")
        payment.addReference(account, "From")
        payment2.addReference(account, "From")

        brels = account.getBRelationships()
        self.assertEquals(brels, ['From'])
        brefs = account.getBRefs('From')
        # The order is not defined, which can lead to spurious test
        # failures, but we do not care about the order.
        self.assertEquals(len(brefs), 2)
        self.failUnless(payment in brefs)
        self.failUnless(payment2 in brefs)

        brels = payment.getBRelationships()
        self.assertEquals(brels, ['Owns'])
        brefs = payment.getBRefs('Owns')
        self.assertEquals(brefs, [invoice])

        brels = payment2.getBRelationships()
        self.assertEquals(brels, ['Owns'])
        brefs = payment2.getBRefs('Owns')
        self.assertEquals(brefs, [future_payment])

        invoice.deleteReference(payment, "Owns")

        self.assertEquals(invoice.getRefs(), [future_payment])
        self.assertEquals(payment.getBRefs(), [])

    def test_singleReference(self):
        # If an object is referenced don't record its reference again
        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id='b')

        #Add the same ref twice
        a.addReference(b, "KnowsAbout")
        a.addReference(b, "KnowsAbout")

        self.assertEquals(len(a.getRefs('KnowsAbout')),  1)

        #In this case its a different relationship
        a.addReference(b, 'Flogs')
        self.assertEquals(len(a.getRefs('KnowsAbout')), 1)
        self.assertEquals(len(a.getRefs()), 2)

    def test_multipleReferences(self):
        # If you provide updateReferences=False to addReference, it
        # will add, not replace the reference
        a = makeContent( self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent( self.folder, portal_type='DDocument',title='Foo', id='b')

        #Add the same ref twice
        a.addReference(b, "KnowsAbout", updateReferences=False)
        a.addReference(b, "KnowsAbout", updateReferences=False)

        self.assertEquals(len(a.getRefs('KnowsAbout')),  2)

        #In this case its a different relationship
        a.addReference(b, 'Flogs')
        self.assertEquals(len(a.getRefs('KnowsAbout')), 2)
        self.assertEquals(len(a.getRefs()), 3)


    def test_UIDunderContainment(self):
        # If an object is referenced don't record its reference again
        at = self.portal.archetype_tool

        folder = makeContent( self.folder, portal_type=self.FOLDER_TYPE,
                              title='Foo', id='folder')
        nonRef = makeContent( folder, portal_type='Document',
                              title='Foo', id='nonRef')

        fuid = folder.UID()
        nuid = nonRef.UID()
        # We expect this to break, an aq_explicit would fix it but
        # we can't change the calling convention
        # XXX: but proxy index could
        # XXX: assert fuid != nuid

    def test_hasRelationship(self):
        a = makeContent(self.folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent(self.folder, portal_type='DDocument',title='Foo', id='b')
        c = makeContent(self.folder, portal_type='DDocument',title='Foo', id='c')

        # Two made up kinda refs
        a.addReference(b, "KnowsAbout")

        self.assertEquals(a.hasRelationshipTo(b), 1)
        self.assertEquals(a.hasRelationshipTo(b, "KnowsAbout"), 1)
        self.assertEquals(a.hasRelationshipTo(b, "Foo"), 0)
        self.assertEquals(a.hasRelationshipTo(c), 0)
        self.assertEquals(a.hasRelationshipTo(c, "KnowsAbout"), 0)

        # XXX HasRelationshipFrom  || ( 1 for ref 2 for bref?)

    def test_folderishDeleteCleanup(self):
        self.folder.invokeFactory(type_name="Folder", id="reftest")
        folder = getattr(self.folder, "reftest")

        a = makeContent(folder, portal_type='DDocument',title='Foo', id='a')
        b = makeContent(folder, portal_type='DDocument',title='Bar', id='b')
        a.addReference(b, "KnowsAbout")

        # Again, lets assert the sanity of the UID and Ref Catalogs
        uc = self.portal.uid_catalog
        rc = self.portal.reference_catalog

        uids = uc.uniqueValuesFor('UID')
        self.failUnless(a.UID() in uids, (a.UID(), uids))
        self.failUnless(b.UID() in uids, (b.UID(), uids))

        uids = rc.uniqueValuesFor('UID')
        refs = rc(dict(UID=uids))
        self.assertEquals(len(refs), 1)
        ref = refs[0].getObject()
        self.assertEquals(ref.targetUID, b.UID())
        self.assertEquals(ref.sourceUID, a.UID())

        # Now Kill the folder and make sure it all went away
        self.folder._delObject("reftest")
        self.verifyBrains()

        uids = rc.uniqueValuesFor('UID')
        self.assertEquals(len(uids), 0)

    def test_reindexUIDCatalog(self):
        catalog = self.portal.uid_catalog

        doc = makeContent(self.folder,
                          portal_type='DDocument',
                          id='demodoc')
        doc.update(title="sometitle")
        brain = catalog(dict(UID=doc.UID()))[0]
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

        field = dummy.Schema()['adds']

        expected = DisplayList([
            (test123.UID(), test123.getId()),
            (test124.UID(), test124.getId()),
            (test125.UID(), test125.getId()),
            (dummy.UID(), dummy.getId()),
            ])

        got = field.Vocabulary(dummy)
        self.assertEquals(got, expected)

        # We should have the option of nothing
        field = field.copy()
        field.required = 0
        field.multiValued = 0

        expected = DisplayList([
            (test123.UID(), test123.getId()),
            (test124.UID(), test124.getId()),
            (test125.UID(), test125.getId()),
            (dummy.UID(), dummy.getId()),
            ('', u'label_no_reference'),
            ])
        self.assertEquals(field.Vocabulary(dummy), expected)

        field = field.copy()
        field.vocabulary_display_path_bound = 1
        expected = DisplayList([
            (test123.UID(), test123.getId()),
            (test124.UID(), test124.getId()),
            (test125.UID(), test125.getId()),
            (dummy.UID(), dummy.getId()),
            ('', u'label_no_reference'),
            ])
        self.failIfEqual(field.Vocabulary(dummy), expected)
        field.vocabulary_display_path_bound = -1
        self.assertEquals(field.Vocabulary(dummy), expected)

    def test_noReferenceAfterDelete(self):
        # Deleting target should delete reference
        # added by GL
        a = makeContent(self.folder, portal_type='DDocument', id='a')
        b = makeContent(self.folder, portal_type='DDocument', id='b')
        a.addReference(b)
        self.folder._delObject('b')

        self.failUnlessEqual(a.getRefs(), [])

    def test_noBackReferenceAfterDelete(self):
        # Deleting source should delete back reference
        # added by GL
        a = makeContent(self.folder, portal_type='DDocument', id='a')
        b = makeContent(self.folder, portal_type='DDocument', id='b')
        a.addReference(b)
        self.folder._delObject('a')

        self.failUnlessEqual(b.getBRefs(), [])

    def test_copyKeepsReferences(self):
        # when copied a pasted object should NOT lose all references
        # if keepReferencesOnCopy is set
        # added by DaftDog (for plone tracker issue  #5180)
        org_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Origin folder',
                                 id='org_folder')
        dst_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Destination folder',
                                 id='dst_folder')
        a = makeContent(org_folder, portal_type='DDocument', id='a')
        b = makeContent(org_folder, portal_type='DDocument', id='b')
        related_field = a.getField('related')
        related_field.set(a, b.UID())

        self.failUnlessEqual(b.getBRefs(), [a])
        self.failUnlessEqual(a.getRefs(), [b])

        cb = org_folder.manage_copyObjects(ids=['a'])
        dst_folder.manage_pasteObjects(cb_copy_data=cb)
        copy_a = getattr(dst_folder, 'a')

        # The copy should get a new UID
        a_uid = a.UID()
        ca_uid = copy_a.UID()
        self.failIf(a_uid == ca_uid, (a_uid, ca_uid))

        # The copy should have the same references
        self.failUnlessEqual(a.getRefs(), copy_a.getRefs())
        self.failUnless(copy_a in b.getBRefs())


        # Original object should keep references
        self.failUnlessEqual(a.getRefs(), [b])
        # Original non-copied object should point to both the original and the copied object
        self.failUnlessEqual(b.getBRefs(), [a, copy_a])

    def test_copyPasteSupport(self):
        # copy/paste behaviour test
        # in another folder, pasted object should lose all references
        # added by GL (for bug #985393)
        org_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Origin folder',
                                 id='org_folder')
        dst_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Destination folder',
                                 id='dst_folder')
        a = makeContent(org_folder, portal_type='DDocument', id='a')
        b = makeContent(org_folder, portal_type='DDocument', id='b')
        a.addReference(b)

        self.failUnlessEqual(b.getBRefs(), [a])
        self.failUnlessEqual(a.getRefs(), [b])

        cb = org_folder.manage_copyObjects(ids=['a'])
        dst_folder.manage_pasteObjects(cb_copy_data=cb)
        copy_a = getattr(dst_folder, 'a')

        # The copy should get a new UID
        a_uid = a.UID()
        ca_uid = copy_a.UID()
        self.failIf(a_uid == ca_uid, (a_uid, ca_uid))

        # The copy shouldn't have references
        self.failUnlessEqual(copy_a.getRefs(), [])
        self.failIf(copy_a in b.getBRefs())


        # Original object should keep references
        self.failUnlessEqual(a.getRefs(), [b])
        self.failUnlessEqual(b.getBRefs(), [a])

    def test_cutPasteSupport(self):
        # cut/paste behaviour test
        # in another folder, pasted object should keep the references
        # added by GL (for bug #985393)
        org_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Origin folder',
                                 id='org_folder')
        dst_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Destination folder',
                                 id='dst_folder')
        a = makeContent(org_folder, portal_type='DDocument', id='a')
        b = makeContent(org_folder, portal_type='DDocument', id='b')
        a.addReference(b)
        transaction.savepoint(optimistic=True)
        cb = org_folder.manage_cutObjects(ids=['a'])
        dst_folder.manage_pasteObjects(cb_copy_data=cb)
        copy_a = getattr(dst_folder, 'a')

        self.failUnlessEqual(copy_a.getRefs(), [b])
        self.failUnlessEqual(b.getBRefs(), [copy_a])

    def test_folderCopyPasteSupport(self):
        # copy/paste behaviour test
        # sub-objects of copy/pasted folders should lose all references,
        # and duplicate refs should not be created on the original object.
        org_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Origin folder',
                                 id='org_folder')
        dst_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Destination folder',
                                 id='dst_folder')
        my_folder = makeContent(org_folder, portal_type=self.FOLDER_TYPE,
                                                             id='my_folder')
        a = makeContent(my_folder, portal_type='DDocument', id='a')
        b = makeContent(my_folder, portal_type='DDocument', id='b')
        a.addReference(b)

        self.failUnlessEqual(b.getBRefs(), [a])
        self.failUnlessEqual(a.getRefs(), [b])

        cb = org_folder.manage_copyObjects(ids=['my_folder'])
        dst_folder.manage_pasteObjects(cb_copy_data=cb)
        copy_folder = getattr(dst_folder, 'my_folder')
        copy_a = getattr(copy_folder, 'a')

        # The copy should get a new UID
        a_uid = a.UID()
        ca_uid = copy_a.UID()
        self.failIf(a_uid == ca_uid, (a_uid, ca_uid))

        # The copy shouldn't have references
        self.failUnlessEqual(copy_a.getRefs(), [])
        self.failIf(copy_a in b.getBRefs())

        #The copy's uid should have changed
        self.failIf(ca_uid == a_uid)

        # Original object should keep references
        self.failUnlessEqual(a.getRefs(), [b])
        self.failUnlessEqual(b.getBRefs(), [a])

    def test_folderCutPasteSupport(self):
        # copy/paste behaviour test
        # sub-objects of copy/pasted folders should lose all references,
        # and duplicate refs should not be created on the original object.
        org_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Origin folder',
                                 id='org_folder')
        dst_folder = makeContent(self.folder,
                                 portal_type=self.FOLDER_TYPE,
                                 title='Destination folder',
                                 id='dst_folder')
        my_folder = makeContent(org_folder, portal_type=self.FOLDER_TYPE,
                                                             id='my_folder')
        a = makeContent(my_folder, portal_type='DDocument', id='a')
        b = makeContent(my_folder, portal_type='DDocument', id='b')
        a.addReference(b)

        self.failUnlessEqual(b.getBRefs(), [a])
        self.failUnlessEqual(a.getRefs(), [b])
        a_uid = a.UID()

        transaction.savepoint(optimistic=True)
        cb = org_folder.manage_cutObjects(ids=['my_folder'])
        dst_folder.manage_pasteObjects(cb_copy_data=cb)
        copy_folder = getattr(dst_folder, 'my_folder')
        copy_a = getattr(copy_folder, 'a')
        copy_b = getattr(copy_folder, 'b')
        ca_uid = copy_a.UID()

        # The copy shouldn't have references
        self.failUnlessEqual(copy_a.getRefs(), [copy_b])
        self.failUnlessEqual(copy_b.getBRefs(), [copy_a])

        #The copy's uid should have changed
        self.failUnless(ca_uid == a_uid, (a_uid, ca_uid))


class SimpleFolderReferenceableTests(BaseReferenceableTests):
    FOLDER_TYPE = 'SimpleFolder'

class SimpleBTreeFolderReferenceableTests(BaseReferenceableTests):
    FOLDER_TYPE = 'SimpleBTreeFolder'

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SimpleFolderReferenceableTests))
    suite.addTest(makeSuite(SimpleBTreeFolderReferenceableTests))
    return suite
