# -*- coding: ISO-8859-1 -*-
# XXX change encoding to UTF-8
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

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from test_classgen import Dummy

from Products.Archetypes.atapi import *
from Products.PortalTransforms.data import datastream


class FakeTransformer:
    def __init__(self, expected):
        self.expected = expected

    def convertTo(self, target_mimetype, orig, data=None, object=None, **kwargs):
        assert orig == self.expected, '????'
        if data is None:
            data = datastream('test')
        data.setData(orig)
        return data


class UnicodeStringFieldTest(ATSiteTestCase):

    def test_set(self):
        instance = Dummy()
        f = StringField('test')
        f.set(instance, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.get(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), 'héhéhé')
        f.set(instance, 'héhéhé', encoding='ISO-8859-1')
        self.failUnlessEqual(f.get(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), 'héhéhé')
        f.set(instance, u'héhéhé')
        self.failUnlessEqual(f.get(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), 'héhéhé')


class UnicodeLinesFieldTest(ATSiteTestCase):

    def test_set1(self):
        instance = Dummy()
        f = LinesField('test')
        f.set(instance, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        out = ('h\xc3\xa9h\xc3\xa9h\xc3\xa9',)
        iso = ('héhéhé',)
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)
        f.set(instance, 'héhéhé', encoding='ISO-8859-1')
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)
        f.set(instance, u'héhéhé')
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)

    def test_set2(self):
        instance = Dummy()
        f = LinesField('test')
        f.set(instance, ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        out = ('h\xc3\xa9h\xc3\xa9h\xc3\xa9',)
        iso = ('héhéhé',)
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)
        f.set(instance, ['héhéhé'], encoding='ISO-8859-1')
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)
        f.set(instance, [u'héhéhé'])
        self.failUnlessEqual(f.get(instance), out)
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), iso)


class UnicodeTextFieldTest(ATSiteTestCase):

    def test_set(self):
        instance = Dummy()
        f = TextField('test')
        f.set(instance, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9', mimetype='text/plain')
        self.failUnlessEqual(f.getRaw(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.getRaw(instance, encoding="ISO-8859-1"), 'héhéhé')
        f.set(instance, 'héhéhé', encoding='ISO-8859-1', mimetype='text/plain')
        self.failUnlessEqual(f.getRaw(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.getRaw(instance, encoding="ISO-8859-1"), 'héhéhé')
        f.set(instance, u'héhéhé', mimetype='text/plain')
        self.failUnlessEqual(f.getRaw(instance), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.getRaw(instance, encoding="ISO-8859-1"), 'héhéhé')


class UnicodeBaseUnitTest(ATSiteTestCase):

    def afterSetUp(self):
        self.instance = Dummy().__of__(self.portal)
        self.bu = BaseUnit('test', 'héhéhé', self.instance,
                           mimetype='text/plain', encoding='ISO-8859-1')

    def test_store(self):
        """check non binary string are stored as unicode"""
        self.failUnless(type(self.bu.raw) is type(u''))

    def test_getRaw(self):
        """check bu.getRaw return the ustring encoded with the default charset
        or the specified one if any
        """
        self.failUnlessEqual(self.bu.getRaw(), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(self.bu.getRaw('ISO-8859-1'), 'héhéhé')

    def test_transform(self):
        """check the string given to the transformer is encoded using its
        original encoding, and finally returned using the default charset
        """
        self.instance.portal_transforms = FakeTransformer('héhéhé')
        transformed = self.bu.transform(self.instance, 'text/plain')
        self.failUnlessEqual(transformed, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(UnicodeStringFieldTest))
    suite.addTest(makeSuite(UnicodeLinesFieldTest))
    suite.addTest(makeSuite(UnicodeTextFieldTest))
    suite.addTest(makeSuite(UnicodeBaseUnitTest))
    return suite
