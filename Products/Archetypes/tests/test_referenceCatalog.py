"""
Unittests for a reference Catalog

$Id: test_referenceCatalog.py,v 1.6 2004/01/19 17:59:29 bcsaller Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')

from Acquisition import aq_base
from Products.Archetypes.tests.test_sitepolicy import makeContent
import Products.Archetypes.config as config
from Products.Archetypes.references import HoldingReference, CascadeReference
from Products.Archetypes.exceptions import ReferenceException
from OFS.ObjectManager import BeforeDeleteException


class ReferenceCatalogTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager(None, user)

    def test_create(self):
        site = self.getPortal()
        rc = getattr(site, config.REFERENCE_CATALOG)
        uc = getattr(site, config.UID_CATALOG)

        self.failUnless(rc is not None)

        id1 = "firstObject"
        obj = makeContent(site, portal_type='Fact', id=id1)
        self.failUnless(obj.UID())

        brains = uc(UID=obj.UID())
        self.failUnless(len(brains) == 1)

        id2 = "secondObject"
        obj2 = makeContent(site, portal_type='Fact', id=id2)

        obj.addReference(obj2, 'testRelationship', foo="bar")

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

        #Now force a rename/move of the each object and then test the refs again
        #This takes some voodoo black magic in a testing environment
        # MAGIC
        obj._p_jar = site._p_jar = self.app._p_jar
        new_oid = self.app._p_jar.new_oid
        obj._p_oid = new_oid()

        obj2._p_jar = site._p_jar = self.app._p_jar
        new_oid = self.app._p_jar.new_oid
        obj2._p_oid = new_oid()
        # /MAGIC

        #Rename can't invalidate UID or refernces
        obj.setId('new1')
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


    def test_holdingref(self):
        site = self.getPortal()
        rc = getattr(site, config.REFERENCE_CATALOG)
        uc = getattr(site, config.UID_CATALOG)

        obj1 = makeContent(site, portal_type='Fact', id='obj1')
        obj2 = makeContent(site, portal_type='Fact', id='obj2')

        obj1.addReference(obj2, relationship="uses", referenceClass=HoldingReference)

        self.failUnless(obj2 in obj1.getRefs('uses'))

        # a holding reference says obj2 can't be deleted cause its held
        try:
            site._delObject(obj2.id)
        except BeforeDeleteException, E:
            pass
        else:
            raise AssertionError("holding reference didn't hold")

        #and just check to make sure its still there
        self.failUnless(hasattr(site, obj2.id))

        obj3 = makeContent(site, portal_type='Fact', id='obj3')
        obj4 = makeContent(site, portal_type='Fact', id='obj4')

        obj3.addReference(obj4, relationship="uses", referenceClass=CascadeReference)

        site.manage_delObjects(obj3.id)
        items = site.contentIds()
        self.failIf(obj3.id in items)
        self.failIf(obj4.id in items)

    def test_delete(self):
        site = self.getPortal()
        rc = getattr(site, config.REFERENCE_CATALOG)
        uc = getattr(site, config.UID_CATALOG)

        obj1 = makeContent(site, portal_type='Fact', id='obj1')
        obj2 = makeContent(site, portal_type='Fact', id='obj2')

        uid1 = obj1.UID()
        uid2 = obj2.UID()


        #Make a reference
        obj1.addReference(obj2, relationship="example")

        #and clean it up
        site._delObject(obj1.id)

        # Assert that the reference is gone, that the UID is gone and
        # that the content is gone
        self.failUnless(obj2.getBRefs() == None)
        self.failIf(obj1.id in site.contentIds())

        self.failIf(uid1 in uc.uniqueValuesFor('UID'))
        self.failUnless(uid2 in uc.uniqueValuesFor('UID'))

        sourceRefs = rc(sourceUID = uid1)
        targetRefs = rc(targetUID = uid1)

        assert len(sourceRefs) == 0
        assert len(targetRefs) == 0

        #also make sure there is nothing in the reference Catalog
        assert len(rc.getReferences(uid1)) == 0
        assert len(rc.getBackReferences(uid1)) == 0
        assert len(rc.getReferences(uid2)) == 0
        assert len(rc.getBackReferences(uid2)) == 0
        


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ReferenceCatalogTests))
        return suite
