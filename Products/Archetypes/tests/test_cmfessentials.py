"""Tests that rely on CMFTestCase rather than PloneTestCase."""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.CMFCore import CMFCorePermissions


class TestPermissions(ATSiteTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        # install AT within portal
        self.login()
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
        self.failUnless(checkPerm(CMFCorePermissions.View, content))
        self.failUnless(checkPerm(CMFCorePermissions.AccessContentsInformation, content))
        self.failUnless(checkPerm(CMFCorePermissions.ModifyPortalContent, content))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPermissions))
    return suite

if __name__ == '__main__':
    framework()
