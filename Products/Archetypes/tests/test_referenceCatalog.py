##########################################################################
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
##########################################################################

from zope import component
from zope import interface
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from plone.indexer.interfaces import IIndexableObject
from Products.ZCatalog.interfaces import IZCatalog

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.Archetypes import config
from Products.Archetypes.references import HoldingReference, CascadeReference
from OFS.ObjectManager import BeforeDeleteException
import transaction

from plone.uuid.interfaces import IAttributeUUID, IUUID
from plone.indexer import wrapper
from Acquisition import Explicit


@interface.implementer(IAttributeUUID)
class DexterityLike(Explicit):
    """Create a new class non based on Archetypes"""

    def __init__(self):
        self.id = "myid"
        self.portal_type = "dexterity_like"
        self.path = []

    def Title(self):
        return u"My dexterity like content"

    def getPhysicalPath(self):
        if self.path[-1] != self.id:
            self.path.append(self.id)
        return self.path

    def manage_fixupOwnershipAfterAdd(self):
        pass

    def getId(self):
        return self.id


class ReferenceCatalogTests(ATSiteTestCase):

    def afterSetUp(self):
        # register the test class as indexable with plone.indexer default
        sm = component.getSiteManager()
        sm.registerAdapter(factory=wrapper.IndexableObjectWrapper,
                           required=(interface.Interface, IZCatalog),
                           provided=IIndexableObject)

    def verifyBrains(self):
        uc = getattr(self.portal, config.UID_CATALOG)
        rc = getattr(self.portal, config.REFERENCE_CATALOG)

        # Verify all UIDs resolve
        uids = uc.uniqueValuesFor('UID')
        brains = uc(dict(UID=uids))
        objects = [b.getObject() for b in brains]
        self.assertFalse(None in objects, """bad uid resolution""")
        for b in brains:
            if b.getPath().startswith('/'):
                print "Bad Brain", b, b.getObject()

        # Verify all references resolve
        uids = rc.uniqueValuesFor('UID')
        brains = rc(dict(UID=uids))
        objects = [b.getObject() for b in brains]
        self.assertFalse(None in objects, """bad ref catalog resolution""")

    def test_create(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        self.assertTrue(rc is not None)

        id1 = "firstObject"
        obj = makeContent(self.folder, portal_type='Fact', id=id1)
        self.assertTrue(obj.UID())

        brains = uc(UID=obj.UID())
        self.assertTrue(len(brains) == 1)

        id2 = "secondObject"
        obj2 = makeContent(self.folder, portal_type='Fact', id=id2)

        self.verifyBrains()
        obj.addReference(obj2, 'testRelationship', foo="bar")
        self.verifyBrains()
        uid1 = obj.UID()
        uid2 = obj2.UID()

        uids = rc.uniqueValuesFor('UID')
        brains = rc(dict(UID=uids))

        ref = brains[0].getObject()
        self.assertTrue(ref.sourceUID == uid1)
        self.assertTrue(ref.targetUID == uid2)

        # Check the metadata
        self.assertTrue(ref.foo == "bar")

        unqualified = obj.getRefs()
        byRel = obj.getRefs('testRelationship')
        assert unqualified[0] == byRel[0] == ref.getTargetObject()

        back = obj2.getBRefs()
        self.assertTrue(back[0] == obj)

        self.assertTrue(obj.reference_url().endswith(uid1))

        # Make sure all objects have _p_oids and _p_jars
        transaction.savepoint(optimistic=True)

        # Rename can't invalidate UID or references
        self.verifyBrains()
        obj.setId('new1')
        self.verifyBrains()

        self.assertTrue(obj.getId() == 'new1')
        self.assertTrue(obj.UID() == uid1)

        b = obj.getRefs()
        self.assertTrue(b[0].UID() == uid2)

        obj2.setId('new2')
        self.assertTrue(obj2.getId() == 'new2')
        self.assertTrue(obj2.UID() == uid2)

        b = obj2.getBRefs()

        self.assertTrue(b[0].UID() == uid1)

        # Add another reference with a different relationship (and the
        # other direction)

        obj2.addReference(obj, 'betaRelationship', this="that")
        b = obj2.getRefs('betaRelationship')
        self.assertTrue(b[0].UID() == uid1)
        b = obj.getBRefs('betaRelationship')
        refs = rc.getBackReferences(obj, 'betaRelationship')
        # objs back ref should be obj2
        self.assertTrue(refs[0].sourceUID == b[0].UID() == uid2)
        self.verifyBrains()

    def test_holdingref(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        obj1 = makeContent(self.folder, portal_type='Fact', id='obj1')
        obj2 = makeContent(self.folder, portal_type='Fact', id='obj2')

        obj1.addReference(obj2, relationship="uses",
                          referenceClass=HoldingReference)

        self.assertTrue(obj2 in obj1.getRefs('uses'))

        # a holding reference says obj2 can't be deleted cause its held
        try:
            self.folder._delObject(obj2.id)
        except BeforeDeleteException, E:
            pass
        else:
            raise AssertionError("holding reference didn't hold")

        # and just check to make sure its still there
        self.assertTrue(hasattr(self.folder, obj2.id))

        obj3 = makeContent(self.folder, portal_type='Fact', id='obj3')
        obj4 = makeContent(self.folder, portal_type='Fact', id='obj4')

        obj3.addReference(obj4, relationship="uses",
                          referenceClass=CascadeReference)

        self.folder.manage_delObjects(obj3.id)
        items = self.folder.contentIds()
        self.assertFalse(obj3.id in items)
        self.assertFalse(obj4.id in items)

    def test_cascaderef(self):
        my1stfolder = makeContent(
            self.folder, portal_type='SimpleFolder', id='my1stfolder')
        obj5 = makeContent(my1stfolder, portal_type='Fact', id='obj5')
        my2ndfolder = makeContent(
            self.folder, portal_type='SimpleFolder', id='my2ndfolder')
        obj6 = makeContent(my2ndfolder, portal_type='Fact', id='obj6')
        obj5.addReference(obj6, relationship="uses",
                          referenceClass=CascadeReference)
        my1stfolder.manage_delObjects(['obj5'])
        items = my1stfolder.contentIds()
        self.assertFalse('obj5' in items)
        items = my2ndfolder.contentIds()
        self.assertFalse('obj6' in items)

    def test_delete(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        obj1 = makeContent(self.folder, portal_type='Fact', id='obj1')
        obj2 = makeContent(self.folder, portal_type='Fact', id='obj2')

        uid1 = obj1.UID()
        uid2 = obj2.UID()

        # Make a reference
        obj1.addReference(obj2, relationship="example")

        # and clean it up
        self.folder._delObject(obj1.id)

        # Assert that the reference is gone, that the UID is gone and
        # that the content is gone
        self.assertTrue(obj2.getBRefs() == [])
        self.assertFalse(obj1.id in self.folder.contentIds())

        self.assertFalse(uid1 in uc.uniqueValuesFor('UID'))
        self.assertTrue(uid2 in uc.uniqueValuesFor('UID'))

        sourceRefs = rc(sourceUID=uid1)
        targetRefs = rc(targetUID=uid1)

        assert len(sourceRefs) == 0
        assert len(targetRefs) == 0

        # also make sure there is nothing in the reference Catalog
        assert len(rc.getReferences(uid1)) == 0
        assert len(rc.getBackReferences(uid1)) == 0
        assert len(rc.getReferences(uid2)) == 0
        assert len(rc.getBackReferences(uid2)) == 0

    def test_custome_metadata(self):
        # create two objects
        # make ref from one object to the other
        # place a custom attribute on the reference
        # update schemas
        # test if attribute still exists on the reference object
        rc = self.portal.reference_catalog

        obj1 = makeContent(self.folder, portal_type='Refnode',
                           id='one')
        uid = obj1.UID()
        obj2 = makeContent(self.folder, portal_type='Refnode', id='two')
        uid2 = obj2.UID()
        # create reference
        obj1.update(link=[obj2.UID()])
        ref = rc.getReferences(obj1)[0]
        ref.attribute1 = "some_value"
        ruid = ref.UID()
        self.assertTrue(ref.attribute1 == 'some_value')

        transaction.savepoint(optimistic=True)
        # update schema
        self.app.REQUEST.form['Archetypes.Refnode'] = 1
        self.app.REQUEST.form['update_all'] = 1
        self.portal.archetype_tool.manage_updateSchema(
            REQUEST=self.app.REQUEST)
        del obj1

        # get the reference for obj1
        obj1 = rc.lookupObject(uid)
        refs = rc.getReferences(obj1, relationship=obj1.Schema()[
                                'link'].relationship)
        ref = refs[0]
        ruid2 = ref.UID()
        assert ruid == ruid2, """ref uid got reassigned"""
        # check for the attribute
        self.assertTrue(hasattr(ref, 'attribute1'),
                        'Custom attribute on reference object is lost during schema update')
        self.assertEqual(ref.attribute1, 'some_value')

    def test_sortable_references(self):
        obj1 = makeContent(self.folder, portal_type='Refnode', id='refone')
        obj2 = makeContent(self.folder, portal_type='Refnode', id='reftwo')
        obj3 = makeContent(self.folder, portal_type='Refnode', id='refthree')
        obj4 = makeContent(self.folder, portal_type='Refnode', id='reffour')

        o2U = obj2.UID()
        o3U = obj3.UID()
        o4U = obj4.UID()

        links1 = [o2U, o3U, o4U]
        obj1.update(sortedlinks=links1)
        self.assertEqual(obj1.getRawSortedlinks(), links1)

        links2 = [o4U, o3U, o2U]
        obj1.update(sortedlinks=links2)
        self.assertEqual(obj1.getRawSortedlinks(), links2)

        links3 = [o3U, o2U]
        obj1.update(sortedlinks=links3)
        self.assertEqual(obj1.getRawSortedlinks(), links3)

    def test_TitleIndexer(self):
        uc = getattr(self.portal, config.UID_CATALOG)
        dext = DexterityLike()
        dext.path = list(self.folder.getPhysicalPath())
        self.folder[dext.id] = dext
        uc.catalog_object(dext, '/'.join(dext.getPhysicalPath()))
        results = uc(Title=dext.Title())
        self.assertTrue(len(results) == 1)
        self.assertTrue(type(dext.Title()) == unicode)
        self.assertTrue(type(results[0].Title) == str)

    def test_UIDIndexer(self):
        uc = getattr(self.portal, config.UID_CATALOG)
        dext = DexterityLike()
        dext.path = list(self.folder.getPhysicalPath())
        self.folder[dext.id] = dext
        notify(ObjectCreatedEvent(dext))  # it supposed to add uuid attribute

        # catalog dext instance
        uc.catalog_object(dext, '/'.join(dext.getPhysicalPath()))

        # check lookup
        uuid = IUUID(dext, None)
        results = uc(UID=uuid)

        self.assertTrue(len(results) == 1)
        self.assertTrue(results[0].UID == uuid)
        self.assertTrue(results[0].Title == str(dext.Title()))

    def test_reference_non_archetypes_content(self):
        # create a archetype based content instance
        ob = makeContent(self.folder, portal_type='DDocument', id='mydocument')
        uc = getattr(self.portal, config.UID_CATALOG)
        uc.catalog_object(ob, '/'.join(ob.getPhysicalPath()))
        # create a non archetype based content
        dext = DexterityLike()
        dext.path = list(self.folder.getPhysicalPath())
        self.folder[dext.id] = dext
        notify(ObjectCreatedEvent(dext))  # it supposed to add uuid attribute
        uc.catalog_object(dext, '/'.join(dext.getPhysicalPath()))
        # create the relation between those
        ob.setRelated(dext)
        self.assertEqual(ob.getRelated()[0], dext)
