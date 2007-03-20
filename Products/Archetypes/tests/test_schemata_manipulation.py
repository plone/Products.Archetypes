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

from Products.Archetypes.tests.attestcase import ATTestCase

from Products.Archetypes.atapi import *
from Products.Archetypes.Schema import ManagedSchema

class SchemataManipulationTest( ATTestCase ):

    def afterSetUp(self):
        self.schema = ManagedSchema(
               (StringField('a', schemata='waldi'),
                StringField('d', schemata='nasbaer'),
                StringField('x', schemata='edgar'),
                StringField('b', schemata='waldi'),
                StringField('e', schemata='nasbaer'),
                StringField('y', schemata='edgar'),
                StringField('c', schemata='waldi'),
                StringField('f', schemata='nasbaer'),
                StringField('z', schemata='edgar')
            ))

    def fields2names(self, fields):
        return [f.getName() for f in fields]

    def testBasic(self):
        self.assertEqual(self.fields2names(self.schema.fields()),
                        ['a','d','x', 'b','e','y','c','f','z'])
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar'])
        self.schema.addField(StringField('p', schemata='waldi'))
        self.schema.addField(StringField('hello_world', schemata='helloworld'))
        self.schema.addField(StringField('hello_world1', schemata='helloworld1'))
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar', 'helloworld', 'helloworld1'])

    def testSchemataFields(self):
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('waldi')),
                        ['a', 'b', 'c'])
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('nasbaer')),
                        ['d', 'e', 'f'])
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('edgar')),
                        ['x', 'y', 'z'])
    def testDelField(self):
        self.schema.delField('x')
        self.schema.delField('b')
        self.schema.delField('z')
        self.assertEqual(self.fields2names(self.schema.fields()),
                        ['a','d','e','y','c','f'])
        self.schema.addField(StringField('z'))
        self.schema.addField(StringField('b'))
        self.schema.addField(StringField('x'))
        self.assertEqual(self.fields2names(self.schema.fields()),
                        ['a','d','e','y','c','f','z','b','x'])
        self.schema.delField('b')
        self.schema.delField('z')
        self.schema.delField('x')
        self.assertEqual(self.fields2names(self.schema.fields()),
                        ['a','d','e','y','c','f'])

    def testDelSchemata(self):
        self.schema.delSchemata('nasbaer')
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'edgar'])
        self.schema.addField(StringField('hello_world', schemata='helloworld'))
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'edgar', 'helloworld'])

    def testAddSchemata(self):
        self.schema.addSchemata('otto')
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar', 'otto'])
        self.assertEqual(len(self.schema.getSchemataFields('otto')), 1)

    def testFieldChangeSchemata(self):
        self.schema.changeSchemataForField('z','otto')
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar', 'otto'])
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('otto')), ['z'])
        self.schema.changeSchemataForField('z','waldi')
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar'])

    def testMoveSchemata1(self):
        self.schema.moveSchemata('waldi', -1)
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar'])
        self.schema.moveSchemata('waldi', 1)
        self.assertEqual(self.schema.getSchemataNames(), ['nasbaer', 'waldi', 'edgar'])
        self.schema.moveSchemata('waldi', 1)
        self.assertEqual(self.schema.getSchemataNames(), ['nasbaer', 'edgar', 'waldi'])
        self.schema.moveSchemata('waldi', 1)
        self.assertEqual(self.schema.getSchemataNames(), ['nasbaer', 'edgar', 'waldi'])

    def testMoveSchemata2(self):
        self.schema.moveSchemata('edgar', 1)
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'nasbaer', 'edgar'])
        self.schema.moveSchemata('edgar', -1)
        self.assertEqual(self.schema.getSchemataNames(), ['waldi', 'edgar', 'nasbaer'])
        self.schema.moveSchemata('edgar', -1)
        self.assertEqual(self.schema.getSchemataNames(), ['edgar', 'waldi', 'nasbaer'])
        self.schema.moveSchemata('edgar', -1)
        self.assertEqual(self.schema.getSchemataNames(), ['edgar', 'waldi', 'nasbaer'])

    def testMoveField(self):
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('waldi')), ['a','b','c'])
        self.schema.moveField('a', -1)
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('waldi')), ['a','b','c'])
        self.schema.moveField('a', 1)
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('waldi')), ['b','a','c'])
        self.schema.moveField('a', 1)
        self.assertEqual(self.fields2names(self.schema.getSchemataFields('waldi')), ['b','c','a'])

    def testReplaceField(self):
        f1 = StringField('f1')
        f2 = StringField('f2')
        f3 = StringField('f3')
        self.schema.replaceField('a', f1)
        self.schema.replaceField('e', f2)
        self.schema.replaceField('z', f3)
        self.assertEqual(self.fields2names(self.schema.fields()),
                        ['f1','d','x', 'b','f2','y','c','f','f3'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SchemataManipulationTest))
    return suite
