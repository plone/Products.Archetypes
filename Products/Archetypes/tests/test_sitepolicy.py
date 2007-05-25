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

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.examples import ComplexType as complextype
from Products.Archetypes.ClassGen import generateCtor

from DateTime import DateTime
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl


class SitePolicyTests(ATSiteTestCase):
    demo_types = ['DDocument', 'SimpleType', 'SimpleFolder',
                  'Fact', 'ComplexType']

    # This test sucks, it doesn't test a unit, or assert anything
    # useful --bcsaller
    ##def test_new( self ):
    ##    # catalog should have one entry, for index_html or frontpage
    ##    # and another for Members
    ##    self.assertEqual( len( self.portal.portal_catalog ), 2 )

    def test_availabledemotypes(self):
        portal_types = self.portal.portal_types.listContentTypes()
        for t in self.demo_types:
            self.failUnless(t in portal_types,
                            "%s not available in portal_types." % t)

    def test_creationdemotypes(self):
        for t in self.demo_types:
            content = makeContent(self.folder, portal_type=t, id=t)
            self.failUnless(t in self.folder.contentIds())
            self.failUnless(not isinstance(content, DefaultDublinCoreImpl))

    # XXX Tests for some basic methods. Should be moved to
    # a separate test suite.
    def test_ComplexTypeGetSize(self):
        content = makeContent(self.folder, portal_type='ComplexType', id='ct')
        size = content.get_size()
        now = DateTime()
        content.setExpirationDate(now)
        # subtract 4 because an empty DateTime field has this size
        new_size = size + len(str(now)) - 4
        self.assertEqual(new_size, content.get_size())
        content.setEffectiveDate(now)
        new_size = new_size + len(str(now)) - 4
        self.assertEqual(new_size, content.get_size())
        content.setIntegerfield(100)
        new_size = new_size -1
        self.assertEqual(new_size, content.get_size())
        content.setIntegerfield(1)
        new_size = new_size - 2
        self.assertEqual(new_size, content.get_size())
        text = 'Bla bla bla'
        content.setTextfield(text)
        new_size = new_size + len(text)
        self.assertEqual(new_size, content.get_size())

    def test_SimpleFolderGetSize(self):
        content = makeContent(self.folder, portal_type='SimpleFolder', id='sf')
        size = content.get_size()
        now = DateTime()
        content.setExpirationDate(now)
        new_size = size + len(str(now)) - 4
        self.assertEqual(new_size, content.get_size())
        content.setEffectiveDate(now)
        new_size = new_size + len(str(now)) - 4
        self.assertEqual(new_size, content.get_size())
        text = 'Bla bla bla'
        content.setTitle(text)
        new_size = new_size + len(text)
        self.assertEqual(new_size, content.get_size())

    def test_addComplexTypeCtor(self):
        addComplexType = generateCtor('ComplexType', complextype)
        id = addComplexType(self.folder, id='complex_type',
                            textfield='Bla', integerfield=1,
                            stringfield='A String')
        obj = getattr(self.folder, id)
        self.assertEqual(obj.getTextfield(), 'Bla')
        self.assertEqual(obj.getStringfield(), 'A String')
        self.assertEqual(obj.getIntegerfield(), 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SitePolicyTests))
    return suite
