import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.Archetypes.tests.common import *

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Schema import Schemata, ManagedSchema, getNames
from Products.Archetypes import listTypes

from DateTime import DateTime


class SchemataManipulationTest( ArchetypesTestCase ):

    def setUp(self):
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

if __name__ == '__main__':
    framework()
