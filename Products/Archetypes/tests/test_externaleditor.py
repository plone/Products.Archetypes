import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.interfaces.base import IBaseUnit


class ExternalEditorTest(ATSiteTestCase):

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
