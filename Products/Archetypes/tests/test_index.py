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
from Products.Archetypes.atapi import *
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.TemplateMixin import TemplateMixin
from Products.Archetypes.tests.utils import makeContent
from Products.CMFCore.utils import getToolByName

class ETagTest(ATSiteTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.inst = makeContent(self.portal,
                                portal_type='SimpleType',
                                id='simple_type')


    def test_etag_does_update_reindex_all(self):
        before = self.inst.http__etag(readonly=True)
        self.inst.reindexObject()
        after = self.inst.http__etag(readonly=True)
        self.failIf(before == after)

    def test_etag_doesnt_update_reindex_metadata(self):
        before = self.inst.http__etag(readonly=True)
        self.inst.reindexObject(idxs=['Title'])
        after = self.inst.http__etag(readonly=True)
        self.assertEquals(before, after)

    def test_etag_update_on_edit(self):
        before = self.inst.http__etag(readonly=True)
        self.inst.edit(title='Bla')
        after = self.inst.http__etag(readonly=True)
        self.failIf(before == after)

    def test_etag_update_on_update(self):
        before = self.inst.http__etag(readonly=True)
        self.inst.update(title='Bla')
        after = self.inst.http__etag(readonly=True)
        self.failIf(before == after)

    def test_etag_update_on_processform(self):
        before = self.inst.http__etag(readonly=True)
        self.inst.processForm(data=1, values={'title':'Bla'})
        after = self.inst.http__etag(readonly=True)
        self.failIf(before == after)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ETagTest))
    return suite

if __name__ == '__main__':
    framework()
