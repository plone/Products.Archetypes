"""Tests that rely on CMFTestCase rather than PloneTestCase."""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

try:
    from Products.CMFTestCase import CMFTestCase
except ImportError:
    raise TestPreconditionFailed('test_cmfessentials',
                                 'Cannot import CMFTestCase')

from Products.SiteErrorLog.SiteErrorLog import manage_addErrorLog
from Products.Archetypes.Extensions.Install import install as installArchetypes

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore.CMFCorePermissions \
     import View, AccessContentsInformation, ModifyPortalContent
import Products.CMFCore.CMFCorePermissions as CMFCorePermissions

from Products.Archetypes.tests.ArchetypesTestCase import DEPS, DEPS_OWN

# install products
for product in DEPS + DEPS_OWN:
    CMFTestCase.installProduct(product)
CMFTestCase.setupCMFSite()

class BaseCMFTest(CMFTestCase.CMFTestCase):
    def afterSetUp(self):
        # install AT within portal
        self.loginAsPortalOwner()
        manage_addErrorLog(self.portal)
        self.portal.manage_addProduct['CMFQuickInstallerTool'].manage_addTool(
            'CMF QuickInstaller Tool', None)
        installArchetypes(self.portal, include_demo=1)
        self.logout()
        self.login()


class TestPermissions(BaseCMFTest):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'Complex Type']

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
