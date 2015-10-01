##########################################################################
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
##########################################################################

import time

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.tests.utils import makeContent
from Products.ZCatalog.ZCatalog import manage_addZCatalog


class ETagTest(ATSiteTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.inst = makeContent(self.portal,
                                portal_type='SimpleType',
                                id='simple_type')

    #! time.sleep(1) is needed to get tests running on fast machines

    def test_etag_does_update_reindex_all(self):
        before = self.inst.http__etag(readonly=True)
        time.sleep(1)
        self.inst.reindexObject()
        after = self.inst.http__etag(readonly=True)
        self.assertFalse(before == after)

    def test_etag_update_on_edit(self):
        before = self.inst.http__etag(readonly=True)
        time.sleep(1)
        self.inst.edit(title='Bla')
        after = self.inst.http__etag(readonly=True)
        self.assertFalse(before == after)

    def test_etag_update_on_update(self):
        before = self.inst.http__etag(readonly=True)
        time.sleep(1)
        self.inst.update(title='Bla')
        after = self.inst.http__etag(readonly=True)
        self.assertFalse(before == after)

    def test_etag_update_on_processform(self):
        before = self.inst.http__etag(readonly=True)
        time.sleep(1)
        self.inst.processForm(data=1, values={'title': 'Bla'})
        after = self.inst.http__etag(readonly=True)
        self.assertFalse(before == after)


class ReindexTest(ATSiteTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.inst = makeContent(self.portal,
                                portal_type='SimpleType',
                                id='simple_type')
        self.ct = getToolByName(self.portal, 'portal_catalog')

    def test_reindex_unindexes_old(self):
        ct = self.ct
        self.assertEqual(len(ct(SearchableText='Mosquito')), 0)
        self.inst.edit(title='Mosquito')
        self.assertEqual(len(ct(SearchableText='Mosquito')), 1)
        self.inst.edit(title='Libido')
        self.assertEqual(len(ct(SearchableText='Mosquito')), 0)


class MultiplexTest(ATSiteTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager'])
        manage_addZCatalog(self.portal, 'zope_catalog', 'Zope Catalog')
        self.portal.zope_catalog.addIndex('getId', 'FieldIndex')
        self.tool = self.portal.archetype_tool
        self.pc = getToolByName(self.portal, 'portal_catalog')
        self.zc = getToolByName(self.portal, 'zope_catalog')

    def test_default_catalog(self):
        inst = makeContent(self.portal,
                           portal_type='SimpleType',
                           id='simple_type')

        # Make sure the object is indexed by portal_catalog...
        results = self.pc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), inst)

        # ...but isn't by the zope_catalog
        results = self.zc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 0)

    def test_new_catalog(self):
        # Change SimpleType to use only zope_catalog
        self.tool.setCatalogsByType('SimpleType', ['zope_catalog'])
        inst = makeContent(self.portal,
                           portal_type='SimpleType',
                           id='simple_type')

        # Make sure the object is indexed by the new zope_catalog...
        results = self.zc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), inst)

        # ...but isn't indexed anymore by portal_catalog
        results = self.pc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 0)

    def test_both_catalogs(self):
        # Change SimpleType to use both catalogs
        self.tool.setCatalogsByType('SimpleType',
                                    ['portal_catalog', 'zope_catalog'])
        inst = makeContent(self.portal,
                           portal_type='SimpleType',
                           id='simple_type')

        # Make sure the object is indexed by portal_catalog...
        results = self.pc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), inst)

        # ...and also by the zope_catalog
        results = self.zc.searchResults(dict(getId='simple_type'))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].getObject(), inst)
