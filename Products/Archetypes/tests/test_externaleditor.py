import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import glob
from os import curdir
from os.path import join, abspath, dirname, split

from common import *
from utils import *

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME, USE_NEW_BASEUNIT
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes.interfaces.base import IBaseUnit
from StringIO import StringIO
from Products.Archetypes.tests.test_sitepolicy import makeContent


class ExternalEditorTest(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager(None, user)

    def testExternalEditor(self):
        #really a test that baseobject.__getitem__ returns something
        #which externaleditor can use
        site = self.getPortal()
        obj = makeContent(site, portal_type='SimpleType', id='obj')
        self.failUnless(IBaseUnit.isImplementedBy(obj.body))
        
        

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ExternalEditorTest))
        return suite
