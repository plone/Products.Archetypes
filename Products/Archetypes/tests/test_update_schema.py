import unittest
import Zope

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.Archetypes.Extensions.Install import install as install_archetypes
from Products.CMFCore.utils import getToolByName

#from Products.Archetypes.tests.update_schema import getDir, PROJECTNAME, ADD_CONTENT_PERMISSION
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.public import listTypes, registerType
from Products.ArchetypesTestUpdateSchema.Extensions.Install import install as install_test
import sys, os, shutil

class test_update_schema(SecurityRequestTest):

    site_id = 'test_site'

    def setUp(self):
        SecurityRequestTest.setUp(self)
        if hasattr(self.root, self.site_id):
            self.root.manage_delObjects([self.site_id])
        self.root.manage_addProduct['CMFPlone'].manage_addSite(self.site_id)
        site = self.getSite()
        install_archetypes(site)
        print install_test(site)


    def tearDown(self):
        if hasattr(self.root, self.site_id):
            self.root.manage_delObjects([self.site_id])
            get_transaction().commit()
        # pack the database so it doesn't get huge
        self.root.Control_Panel.Database.manage_pack()
        get_transaction().commit()

        SecurityRequestTest.tearDown(self)


    def getSite(self):
        return getattr(self.root, self.site_id)

    def _setClass(self, version):
        import Products.ArchetypesTestUpdateSchema
        classdir = Products.ArchetypesTestUpdateSchema.getDir()
        dest = os.path.join(classdir, 'TestClass.py')
        pyc = os.path.join(classdir, 'TestClass.pyc')
        src = os.path.join(classdir, 'TestClass%d.py' % version)
        shutil.copyfile(src, dest)
        os.utime(dest,None)
        try:
            os.remove(pyc)
        except:
            pass

        self.root.Control_Panel.Products.ArchetypesTestUpdateSchema.manage_performRefresh()

        # flush the ZODB cache
        self.root.Control_Panel.Database.manage_minimize(0)

#        sys.stdout.write('copying %s to %s\n' % (src, dest))


    def test_detect_schema_change(self):
        site = self.getSite()
        self._setClass(1)

        t1 = makeContent(site, portal_type='TestClass', id='t1')
        get_transaction().commit()

        self.failUnless(t1._isSchemaCurrent())

        site.archetype_tool.manage_updateSchema()
        get_transaction().commit()

        self.failUnless(t1._isSchemaCurrent())

        self._setClass(2)
        get_transaction().commit()

        t1 = site.t1
        self.failIf(t1._isSchemaCurrent())

        t2 = makeContent(site, portal_type='TestClass', id='t2')
        self.failUnless(t2._isSchemaCurrent())
        get_transaction().commit()

        site.archetype_tool.manage_updateSchema()
        get_transaction().commit()

        self.failUnless(t1._isSchemaCurrent())
        

    def test_update_schema(self):
        site = self.getSite()
        self._setClass(1)

        t1 = makeContent(site, portal_type='TestClass', id='t1')
        get_transaction().commit()

        self.failUnless(hasattr(t1, 'a'))
        self.failIf(hasattr(t1, 'b'))

        print site.archetype_tool.manage_updateSchema()
        get_transaction().commit()

        self.failUnless(hasattr(t1, 'a'))
        self.failIf(hasattr(t1, 'b'))

        self._setClass(2)

        t2 = makeContent(site, portal_type='TestClass', id='t2')
        get_transaction().commit()
        self.failUnless(hasattr(t2, 'a'))
        self.failUnless(hasattr(t2, 'b'))

        t1 = site.t1

        self.failUnless(hasattr(t1, 'a'))
        self.failIf(hasattr(t1, 'b'))

        print site.archetype_tool.manage_updateSchema()
        get_transaction().commit()

        self.failUnless(hasattr(t1, 'a'))
        self.failUnless(hasattr(t1, 'b'))
        self.failUnless(hasattr(t1, 'getA'))
        self.failUnless(hasattr(t1, 'getB'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DisplayListTest),
        ))

if __name__ == '__main__':
    unittest.main()        