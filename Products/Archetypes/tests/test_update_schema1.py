import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_update_schema1', 'Cannot import ArcheSiteTestCase')

from Products.Archetypes.Extensions.Install import install as install_archetypes
from Products.CMFCore.utils import getToolByName

from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.public import listTypes, registerType
try:
    from Products.ArchetypesTestUpdateSchema.Extensions.Install import install as install_test
except ImportError:
    raise TestPreconditionFailed('test_update_schema1', 'Cannot import from ArchetypesTestUpdateSchema')
import sys, os, shutil


# We are breaking up the update schema test into 2 separate parts, since
# the product refresh appears to cause strange things to happen when we
# run multiple tests in the same test suite.

class TestUpdateSchema1(ZopeTestCase.Sandboxed, ArcheSiteTestCase):

    def afterSetUp(self):
        qi = getToolByName(self.portal, 'portal_quickinstaller')
        qi.installProduct('ArchetypesTestUpdateSchema')

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

        self.app.Control_Panel.Products.ArchetypesTestUpdateSchema.manage_performRefresh()


    def test_detect_schema_change(self):
        self._setClass(1)

        t1 = makeContent(self.folder, portal_type='TestClass', id='t1')
        self.failUnless(t1._isSchemaCurrent())

        self.portal.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())

        self._setClass(2)

        t1 = self.folder.t1
        self.failIf(t1._isSchemaCurrent())

        t2 = makeContent(self.folder, portal_type='TestClass', id='t2')
        self.failUnless(t2._isSchemaCurrent())

        self.portal.archetype_tool.manage_updateSchema()
        self.failUnless(t1._isSchemaCurrent())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestUpdateSchema1))
    return suite

if __name__ == '__main__':
    framework()
