"""Tests that rely on CMFTestCase rather than PloneTestCase."""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.CMFTestCase import CMFTestCase
from Products.SiteErrorLog.SiteErrorLog import manage_addErrorLog
from Products.Archetypes.Extensions.Install import install as installArchetypes

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.CMFCorePermissions \
     import View, AccessContentsInformation, ModifyPortalContent
import Products.CMFCore.CMFCorePermissions as CMFCorePermissions

class BaseCMFTest(ArcheSiteTestCase):

    def afterSetUp(self):
        # install AT within portal
        self.login()


class TestPermissions(BaseCMFTest):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    def afterSetUp(self):
        BaseCMFTest.afterSetUp(self)

        self.demo_instances = []
        for t in self.demo_types:
            # XXX: Fails with "Unauthorized" exception from
            #      CMFDefault/DiscussionTool.py:84, in overrideDiscussionFor
            #
            #      Note that BaseObject.initializeArchetype has a bare except
            #      that prints out the error instead of letting it through, so
            #      that there is no exception when running the test.
            inst = makeContent(self.folder, portal_type=t, id=t)
            self.demo_instances.append(inst)

    def testPermissions(self):
        content = self.demo_instances[0]
        # XXX: Strangely enough we have correct permissions here, but not so
        #      in initializeArchetype
        self.failUnless(checkPerm(View, content))
        self.failUnless(checkPerm(AccessContentsInformation, content))
        self.failUnless(checkPerm(ModifyPortalContent, content))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPermissions))
    return suite

if __name__ == '__main__':
    framework()
