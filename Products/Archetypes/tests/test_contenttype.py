import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

import unittest
from os import curdir
from os.path import join, abspath, dirname
from Products.Archetypes.public import *
from test_classgen import Dummy, gen_dummy

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
        obj.setAtextfield('Bla', mimetype='text/restructured')
        self.failUnless(obj.getAtextfield().getRaw() == 'Bla')
        self.failUnless(obj.getField('atextfield').getContentType(obj) == 'text/restructured')

    def test_textfieldwithmime2(self):
        obj = self._dummy
        obj.setAtextfield('Bla', mimetype='text/structured')
        self.failUnless(obj.getAtextfield().getRaw() == 'Bla')
        self.failUnless(obj.getField('atextfield').getContentType(obj) == 'text/structured')

    def test_textfieldwithoutmime(self):
        obj = self._dummy
        obj.setAtextfield('Bla')
        self.failUnless(obj.getAtextfield().getRaw() == 'Bla')
        self.failUnless(obj.getField('atextfield').getContentType(obj) == 'text/plain')

    def test_textfielduploadwithoutmime(self):
        file = open(join(_prefix, "input", "rest1.tgz"), 'r')
        obj = self._dummy
        obj.setAtextfield(file)
        file.close()
        self.failUnless(obj.getField('atextfield').getContentType(obj) == 'application/x-tar')

    def test_filefieldwithmime(self):
        obj = self._dummy
        obj.setAfilefield('Bla', mimetype='text/restructured')
        self.failUnless(str(obj.getAfilefield()) == 'Bla')
        self.failUnless(obj.getField('afilefield').getContentType(obj) == 'text/restructured')

    def test_filefieldwithmime2(self):
        obj = self._dummy
        obj.setAfilefield('Bla', mimetype='text/structured')
        self.failUnless(str(obj.getAfilefield()) == 'Bla')
        self.failUnless(obj.getField('afilefield').getContentType(obj) == 'text/structured')

    def test_filefieldwithoutmime(self):
        obj = self._dummy
        obj.setAfilefield('Bla')
        self.failUnless(str(obj.getAfilefield()) == 'Bla')
        self.failUnless(obj.getField('afilefield').getContentType(obj) == 'text/plain')

    def test_filefielduploadwithoutmime(self):
        file = open(join(_prefix, "input", "rest1.tgz"), 'r')
        obj = self._dummy
        obj.setAfilefield(file)
        file.close()
        self.failUnless(obj.getField('afilefield').getContentType(obj) == 'application/x-tar')

    def tearDown(self):
        del self._dummy

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ContentTypeTest),
        ))

if __name__ == '__main__':
    unittest.main()
