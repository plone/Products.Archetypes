# -*- coding: iso8859-1 -*-
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from test_classgen import Dummy


from Products.Archetypes.Field import *
from Products.PortalTransforms.MimeTypesRegistry import MimeTypesRegistry
from Products.Archetypes.BaseUnit import BaseUnit
from Products.PortalTransforms.data import datastream
instance = Dummy()

class FakeTransformer:
    def __init__(self, expected):
        self.expected = expected

    def convertTo(self, target_mimetype, orig, data=None, object=None, **kwargs):
        assert orig == self.expected
        if data is None:
            data = datastream('test')
        data.setData(orig)
        return data
tests = []

class UnicodeStringFieldTest( ArchetypesTestCase ):

    def test_set(self):
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

tests.append(UnicodeStringFieldTest)

class UnicodeLinesFieldTest( ArchetypesTestCase ):

    def test_set1(self):
        f = LinesField('test')
        f.set(instance, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])
        f.set(instance, 'héhéhé', encoding='ISO-8859-1')
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])
        f.set(instance, u'héhéhé')
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])

    def test_set2(self):
        f = LinesField('test')
        f.set(instance, ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])
        f.set(instance, ['héhéhé'], encoding='ISO-8859-1')
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])
        f.set(instance, [u'héhéhé'])
        self.failUnlessEqual(f.get(instance), ['h\xc3\xa9h\xc3\xa9h\xc3\xa9'])
        self.failUnlessEqual(f.get(instance, encoding="ISO-8859-1"), ['héhéhé'])


tests.append(UnicodeLinesFieldTest)

class UnicodeTextFieldTest( ArchetypesTestCase ):

    def test_set(self):
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

tests.append(UnicodeTextFieldTest)

class UnicodeBaseUnitTest(ArchetypesTestCase):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        self.bu = BaseUnit('test', 'héhéhé', instance, mimetype='text/plain', encoding='ISO-8859-1')

    def test_store(self):
        self.failUnless(type(self.bu.raw is type(u'')))

    def test_getRaw(self):
        self.failUnlessEqual(self.bu.getRaw(), 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')
        self.failUnlessEqual(self.bu.getRaw('ISO-8859-1'), 'héhéhé')

    def test_transform(self):
        instance = Dummy()
        instance.portal_transforms = FakeTransformer('héhéhé')
        transformed = self.bu.transform(instance, 'text/plain')
        self.failUnlessEqual(transformed, 'h\xc3\xa9h\xc3\xa9h\xc3\xa9')

tests.append(UnicodeBaseUnitTest)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        for test in tests:
            suite.addTest(unittest.makeSuite(test))
        return suite
