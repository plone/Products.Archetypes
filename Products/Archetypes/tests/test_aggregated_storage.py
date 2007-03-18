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

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.atapi import AggregatedStorage
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import BaseContent
from Products.Archetypes.atapi import registerType


class Dummy(BaseContent):

    def __init__(self, oid, **kwargs):
        BaseContent.__init__(self, oid, **kwargs)
        self.firstname = ''
        self.lastname = ''

    def get_name(self, name, instance, **kwargs):
        """ aggregator """
        return {'whole_name' : instance.firstname + " " + instance.lastname }

    def set_name(self, name, instance, value, **kwargs):
        """ disaggregator """
        try:
            firstname, lastname = value.split(' ')
        except:
            firstname = lastname = ''
        setattr(instance, 'firstname', firstname)
        setattr(instance, 'lastname', lastname)

registerType(Dummy, 'Archetypes')


class AggregatedStorageTestsNoCache(ATSiteTestCase):

    caching = 0

    def afterSetUp(self):
        self._storage = AggregatedStorage(caching=self.caching)
        self._storage.registerAggregator('whole_name', 'get_name')
        self._storage.registerDisaggregator('whole_name', 'set_name')

        schema = Schema( (StringField('whole_name', storage=self._storage),
                         ))

        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])        

        self._instance = mkDummyInContext(klass=Dummy, oid='dummy',
                                          context=self.portal, schema=schema)

    def test_basetest(self):
        field = self._instance.Schema()['whole_name']

        self.assertEqual(field.get(self._instance).strip(), '')
        field.set(self._instance, 'Donald Duck')
        self.assertEqual(self._instance.firstname, 'Donald')
        self.assertEqual(self._instance.lastname, 'Duck')
        self.assertEqual(field.get(self._instance).strip(), 'Donald Duck')

        self._instance.firstname = 'Daniel'
        self._instance.lastname = 'Dosentrieb'
        self.assertEqual(field.get(self._instance).strip(), 'Daniel Dosentrieb')

        field.set(self._instance, 'Bingo Gringo')
        self.assertEqual(self._instance.firstname, 'Bingo')
        self.assertEqual(self._instance.lastname, 'Gringo')


class AggregatedStorageTestsWithCache(AggregatedStorageTestsNoCache):

    caching = 1


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(AggregatedStorageTestsNoCache))
    suite.addTest(makeSuite(AggregatedStorageTestsWithCache))
    return suite
