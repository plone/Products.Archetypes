import unittest
from os import curdir
from os.path import join, abspath, dirname

# this trigger zope imports
from test_classgen import Dummy, gen_dummy

from Products.Archetypes.public import *

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

class ContentTypeTest( unittest.TestCase ):

    def setUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

    def test_textfieldwithmime(self):
        obj = self._dummy
        obj.setAtextfield('Bla', mimetype='text/x-rst')
        self.assertEqual(obj.getField('atextfield').getContentType(obj), 'text/x-rst')
        self.assertEqual(obj.getField('atextfield').getRaw(obj), 'Bla')

    def test_textfieldwithmime2(self):
        obj = self._dummy
        obj.setAtextfield('Bla', mimetype='text/structured')
        self.assertEqual(obj.getField('atextfield').getRaw(obj), 'Bla')
        self.assertEqual(obj.getField('atextfield').getContentType(obj), 'text/structured')

    def test_textfieldwithoutmime(self):
        obj = self._dummy
        obj.setAtextfield('Bla')
        self.assertEqual(str(obj.getField('atextfield').getRaw(obj)), 'Bla')
        self.assertEqual(obj.getField('atextfield').getContentType(obj), 'text/plain')

    def test_textfielduploadwithoutmime(self):
        file = open(join(_prefix, "input", "rest1.tgz"), 'r')
        obj = self._dummy
        obj.setAtextfield(file)
        file.close()
        self.assertEqual(obj.getField('atextfield').getContentType(obj), 'application/x-tar')

    def test_filefieldwithmime(self):
        obj = self._dummy
        obj.setAfilefield('Bla', mimetype='text/x-rst')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(obj.getField('afilefield').getContentType(obj), 'text/x-rst')

    def test_filefieldwithmime2(self):
        obj = self._dummy
        obj.setAfilefield('Bla', mimetype='text/structured')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(obj.getField('afilefield').getContentType(obj), 'text/structured')

    def test_filefieldwithoutmime(self):
        obj = self._dummy
        obj.setAfilefield('Bla')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(obj.getField('afilefield').getContentType(obj), 'text/plain')

    def test_filefielduploadwithoutmime(self):
        file = open(join(_prefix, "input", "rest1.tgz"), 'r')
        obj = self._dummy
        obj.setAfilefield(file)
        file.close()
        self.assertEqual(obj.getField('afilefield').getContentType(obj), 'application/x-tar')

    def tearDown(self):
        del self._dummy

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ContentTypeTest),
        ))

if __name__ == '__main__':
    unittest.main()
