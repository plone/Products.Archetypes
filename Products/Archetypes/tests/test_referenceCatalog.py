"""
Unittests for a reference Catalog

$Id: test_referenceCatalog.py,v 1.8.16.3 2004/05/13 15:59:17 shh42 Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')

from Products.Archetypes import config
from Products.Archetypes.references import HoldingReference, CascadeReference
from Products.Archetypes.exceptions import ReferenceException
from OFS.ObjectManager import BeforeDeleteException


class ReferenceCatalogTests(ArcheSiteTestCase):

    def verifyBrains(self):
        uc = getattr(self.portal, config.UID_CATALOG)
        rc = getattr(self.portal, config.REFERENCE_CATALOG)

        #Verify all UIDs resolve
        brains = uc()
        objects = [b.getObject() for b in brains]
        self.failIf(None in objects, """bad uid resolution""")

        #Verify all references resolve
        brains = rc()
        objects = [b.getObject() for b in brains]
        self.failIf(None in objects, """bad ref catalog resolution""")

    def test_create(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        self.failUnless(rc is not None)

        id1 = "firstObject"
        obj = makeContent(self.folder, portal_type='Fact', id=id1)
        self.failUnless(obj.UID())

        brains = uc(UID=obj.UID())
        self.failUnless(len(brains) == 1)

        id2 = "secondObject"
        obj2 = makeContent(self.folder, portal_type='Fact', id=id2)

        self.verifyBrains()
        obj.addReference(obj2, 'testRelationship', foo="bar")
        self.verifyBrains()
        uid1 = obj.UID()
        uid2 = obj2.UID()

        brains = rc()
        ref = brains[0].getObject()
        self.failUnless(ref.sourceUID == uid1)
        self.failUnless(ref.targetUID == uid2)

        #Check the metadata
        self.failUnless(ref.foo == "bar")

        unqualified = obj.getRefs()
        byRel = obj.getRefs('testRelationship')
        assert unqualified[0] == byRel[0] == ref.getTargetObject()

        back = obj2.getBRefs()
        self.failUnless(back[0] == obj)

        self.failUnless(obj.reference_url().endswith(uid1))

        # Make sure all objects have _p_oids and _p_jars
        get_transaction().commit(1)

        #Rename can't invalidate UID or references
        self.verifyBrains()
        obj.setId('new1')
        self.verifyBrains()

        self.failUnless(obj.getId() == 'new1')
        self.failUnless(obj.UID() == uid1)

        b = obj.getRefs()
        self.failUnless(b[0].UID() == uid2)

        obj2.setId('new2')
        self.failUnless(obj2.getId() == 'new2')
        self.failUnless(obj2.UID() == uid2)

        b = obj2.getBRefs()

        self.failUnless(b[0].UID() == uid1)

        #Add another reference with a different relationship (and the
        #other direction)

        obj2.addReference(obj, 'betaRelationship', this="that")
        b = obj2.getRefs('betaRelationship')
        self.failUnless(b[0].UID() == uid1)
        b = obj.getBRefs('betaRelationship')
        refs = rc.getBackReferences(obj, 'betaRelationship')
        # objs back ref should be obj2
        self.failUnless(refs[0].sourceUID == b[0].UID() == uid2)
        self.verifyBrains()


    def test_holdingref(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        obj1 = makeContent(self.folder, portal_type='Fact', id='obj1')
        obj2 = makeContent(self.folder, portal_type='Fact', id='obj2')

        obj1.addReference(obj2, relationship="uses", referenceClass=HoldingReference)

        self.failUnless(obj2 in obj1.getRefs('uses'))

        # a holding reference says obj2 can't be deleted cause its held
        try:
            self.folder._delObject(obj2.id)
        except BeforeDeleteException, E:
            pass
        else:
            raise AssertionError("holding reference didn't hold")

        #and just check to make sure its still there
        self.failUnless(hasattr(self.folder, obj2.id))

        obj3 = makeContent(self.folder, portal_type='Fact', id='obj3')
        obj4 = makeContent(self.folder, portal_type='Fact', id='obj4')

        obj3.addReference(obj4, relationship="uses", referenceClass=CascadeReference)

        self.folder.manage_delObjects(obj3.id)
        items = self.folder.contentIds()
        self.failIf(obj3.id in items)
        self.failIf(obj4.id in items)

    def test_cascaderef(self):
        my1stfolder = makeContent(self.folder, portal_type='SimpleFolder', id='my1stfolder')
        obj5 = makeContent(my1stfolder, portal_type='Fact', id='obj5')
        my2ndfolder = makeContent(self.folder, portal_type='SimpleFolder', id='my2ndfolder')
        obj6 = makeContent(my2ndfolder, portal_type='Fact', id='obj6')
        obj5.addReference(obj6, relationship="uses", referenceClass=CascadeReference)
        my1stfolder.manage_delObjects(['obj5'])
        items = my1stfolder.contentIds()
        self.failIf('obj5' in items)
        items = my2ndfolder.contentIds()
        self.failIf('obj6' in items)

    def test_delete(self):
        rc = getattr(self.portal, config.REFERENCE_CATALOG)
        uc = getattr(self.portal, config.UID_CATALOG)

        obj1 = makeContent(self.folder, portal_type='Fact', id='obj1')
        obj2 = makeContent(self.folder, portal_type='Fact', id='obj2')

        uid1 = obj1.UID()
        uid2 = obj2.UID()


        #Make a reference
        obj1.addReference(obj2, relationship="example")

        #and clean it up
        self.folder._delObject(obj1.id)

        # Assert that the reference is gone, that the UID is gone and
        # that the content is gone
        self.failUnless(obj2.getBRefs() == [])
        self.failIf(obj1.id in self.folder.contentIds())

        self.failIf(uid1 in uc.uniqueValuesFor('UID'))
        self.failUnless(uid2 in uc.uniqueValuesFor('UID'))

        sourceRefs = rc(sourceUID = uid1)
        targetRefs = rc(targetUID = uid1)

        assert len(sourceRefs) == 0
        assert len(targetRefs) == 0

        #also make sure there is nothing in the reference Catalog
        # XXX Need to double check; _uidFor() errors out on these.
        ##assert len(rc.getReferences(uid1)) == 0
        ##assert len(rc.getBackReferences(uid1)) == 0
        assert len(rc.getReferences(uid2)) == 0
        assert len(rc.getBackReferences(uid2)) == 0


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ReferenceCatalogTests))
    return suite

if __name__ == '__main__':
    framework()
