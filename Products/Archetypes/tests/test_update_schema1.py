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

from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.public import listTypes, registerType
from Products.ArchetypesTestUpdateSchema.Extensions.Install import install as install_test
import sys, os, shutil

# We are breaking up the update schema test into 2 separate parts, since
# the product refresh appears to cause strange things to happen when we
# run multiple tests in the same test suite.

class test_update_schema1(SecurityRequestTest):

    site_id = 'unittest_test_site'
    created_site = 0

    def setUp(self):
        SecurityRequestTest.setUp(self)
        if not hasattr(self.root, self.site_id):
            self.root.manage_addProduct['CMFPlone'].manage_addSite(self.site_id)
            self.created_site = 1
        site = getattr(self.root, self.site_id)
        install_archetypes(site)
        install_test(site)


    def tearDown(self):
        get_transaction().abort()
        # clean things up by hand, since the transaction seems to be getting
        # committed somewhere along the way
        site = getattr(self.root, self.site_id, None)
        if site:
            if hasattr(site, 't1'):
                site.manage_delObjects(['t1'])
            if hasattr(site, 't2'):
                site.manage_delObjects(['t2'])
            if self.created_site:
                self.root.manage_delObjects([self.site_id])
            get_transaction().commit()
        SecurityRequestTest.tearDown(self)


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


    def test_detect_schema_change(self):
        site = getattr(self.root, self.site_id)
        self._setClass(1)

        t1 = makeContent(site, portal_type='TestClass', id='t1')
        self.failUnless(t1._isSchemaCurrent())

        site.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())

        self._setClass(2)

        t1 = site.t1
        self.failIf(t1._isSchemaCurrent())

        t2 = makeContent(site, portal_type='TestClass', id='t2')
        self.failUnless(t2._isSchemaCurrent())

        site.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(test_update_schema1),
        ))

if __name__ == '__main__':
    unittest.main()        