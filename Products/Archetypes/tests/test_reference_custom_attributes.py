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

from Products.Archetypes.tests.test_fields import FakeRequest


class ReferenceCustomAttributesTests(ArcheSiteTestCase):


    def test_attribs(self):
        # create two objects
        # make ref from one object to the other
        # place a custom attribute on the reference
        # update schemas
        # test if attribute still exists on the reference object

        # create objects
        id1='obj1'
        id2='obj2'
        
        obj1 = makeContent(self.folder, portal_type='Refnode', id=id1)
        uid = obj1.UID()
        
        obj2 = makeContent(self.folder, portal_type='Refnode', id=id2)
        
        # create reference
        ref = obj1.addReference(obj2, 'A')
    
        # create the attribute
        ref.attribute1='some_value'

        self.failUnless(ref.attribute1=='some_value')

        # update schema
        self.app.REQUEST.form['Archetypes.Refnode']=1
        self.app.REQUEST.form['update_all']=1
        
        self.portal.archetype_tool.manage_updateSchema(REQUEST=self.app.REQUEST)
        
        # get the reference for obj1
        rc = self.portal.reference_catalog
        obj1 = self.portal.archetype_tool.getObject(uid)
        refs = rc.getReferences(obj1, relationship='A')
        ref = refs[0]
        
        #check for the attribute
        self.failUnless(hasattr(ref, 'attribute1'), 'Custom attribute on reference object is lost during schema update')
        self.assertEqual(ref.attribute1, 'some_value')
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ReferenceCustomAttributesTests))
    return suite

if __name__ == '__main__':
    framework()
