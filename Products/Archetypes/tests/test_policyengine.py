# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase

from Products.Archetypes.atapi import *
from Products.Archetypes.utils import make_uuid

from Products.Archetypes.policy import PolicyEngine, Composer
from Products.Archetypes.policy import SchemaComposer, BehaviorComposer
from Products.Archetypes.policy import ArchetypesPolicyManager
from Products.Archetypes.policy import AxisManager, SourceSet

class MockAxis(AxisManager):
    def __init__(self, **kwargs):
        # container for register'd information
        self._registry = {}
        self._registry.update(kwargs)
        self.uuid = make_uuid()

    def collect(self, identifier, **criteria):
        return SourceSet((self, 0, self.__name__))

class MockTypeAxis(MockAxis):
    __name__ = "type"

class MockContainmentAxis(MockAxis):
    __name__ = "containment"

class SimpleComposer(Composer):
    __name__= "Simple Composer"
    def interested(self, object):
        return True

    def compose(self, sourceSet):
        # return a list with all the source set info
        # ordered by priority
        sourceSet.sort()
        return [b[2] for b in sourceSet], {}

class TestPolicyEngine(ATSiteTestCase):
        def afterSetUp(self):
            # This can go away after the installer bootstraps this
            # process
            ATSiteTestCase.afterSetUp(self)
            self._buildPolicyEngine()


        def _buildPolicyEngine(self):
            portal = self.portal
            self.loginAsPortalOwner()

            pe = PolicyEngine()
            portal._setOb('policy_engine', pe)
            pe = portal._getOb('policy_engine')
            assert pe

            # and associate the default policy manager with the engine
            pm = ArchetypesPolicyManager()
            pm.registerComposer(SimpleComposer())
            pe.registerManager(pm)
            pe.setDefaultPolicyManager(pm.__name__)

            # Log out as manager and in as a normal user
            self.logout()
            self.login()

        def test_basicBuild(self):
            pe = self.portal.policy_engine
            assert pe
            pm = pe.getPolicyManager("archetypesPolicyManager")
            assert pm

        def test_registerAxis(self):
            pe = self.portal.policy_engine
            pe.registerAxis(MockTypeAxis)


        def test_sourceSet(self):
            ss = SourceSet( ("type", 5, None),
                            ("containment", 7, None),
                            ("reference", 1, None),
                        )
            # iter
            assert [b[0] for b in ss] == ["reference",
                                          "type",
                                          "containment"]

            # getitem
            assert ss[0][0] == "reference"

            # (inplace) addition
            tt = SourceSet(("foo", 3, None))
            ss += tt
            assert [b[0] for b in ss] == ["reference",
                                          "foo",
                                          "type",
                                          "containment"]



        def test_provide(self):
            # This is the minimal top level test of the sytem.
            # if it can provide from 1/2/3 axes based on a strategy
            # then the basics work
            pe = self.portal.policy_engine
            pe.registerAxis(MockTypeAxis())
            pe.registerAxis(MockContainmentAxis())
            pm = pe.getDefaultPolicyManager()
            pm.assignAxisPriorities(pe,
                                    type=5,
                                    containment=10)

            policy = pe.getPolicy(None)
            # It just added the elements together
            assert policy == ['type', 'containment']

            pm.assignAxisPriorities(pe,
                                    type=10,
                                    containment=5)
            policy = pe.getPolicy(None)
            # It just added the elements together
            assert policy == ['containment', 'type']


        def test_provideSchema(self):
            # unittest of the schema composer
            # hand build sourceSets, let make sure compose does
            # the expected (sane?) thing

            # Suppose this is type based content
            SchemaA = Schema((
                TextField("body"),
                TextField("teaser")
                ))

            # and Suppose this was containment metadata
            SchemaB = Schema((
                TextField("subject"),
                ))

            # This would be an already collected and prioritized
            # sourceset handed off to the composer
            mta = MockTypeAxis()
            mca = MockContainmentAxis()
            ss = SourceSet((mta, 1, SchemaA),
                           (mca, 2, SchemaB))

            sc = SchemaComposer()
            schema, work = sc.compose(ss)
            all = [f.getName() for f in schema.fields()]
            assert all == ['subject', 'body', 'teaser']

            # look into work and make sure that we can make from the
            # uuid of the fields back to the provider
            assert work[schema['subject'].uuid] == \
                   (mca.uuid, SchemaB.uuid)
            assert work[schema['body'].uuid] == \
                   (mta.uuid, SchemaA.uuid)
            assert work[schema['teaser'].uuid] == \
                   (mta.uuid, SchemaA.uuid)




        def test_eventDrivenUpdate(self):
            # test that a provided policy (schema in this case) is
            # updated when a source changes
            pass




def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPolicyEngine))
    return suite

if __name__ == '__main__':
    framework()

