import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

import glob
from os import curdir
from os.path import join, abspath, dirname, split

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.lib.baseunit import BaseUnit
from Products.Archetypes.interfaces.base import IBaseUnit


class ExternalEditorTest(ArcheSiteTestCase):

    def testExternalEditor(self):
        #really a test that baseobject.__getitem__ returns something
        #which externaleditor can use
        obj = makeContent(self.folder, portal_type='SimpleType', id='obj')
        self.failUnless(IBaseUnit.isImplementedBy(obj.body))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ExternalEditorTest))
    return suite

if __name__ == '__main__':
    framework()
