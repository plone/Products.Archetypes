import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from os import curdir
from os.path import join, abspath, dirname

# this trigger zope imports
from test_classgen import Dummy, gen_dummy, default_text

from Products.Archetypes.atapi import *


class GetFilenameTest(ArchetypesTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

    def test_textfieldwithfilename(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        self.assertEqual(field.getFilename(obj), '')
        self.assertEqual(field.getRaw(obj), default_text)
        obj.setAtextfield('Bla', filename='name.rst')
        self.assertEqual(field.getFilename(obj), 'name.rst')
        self.assertEqual(field.getRaw(obj), 'Bla')

    def test_textfieldwithfilename2(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Ble', filename='eitadiacho.txt')
        self.assertEqual(field.getRaw(obj), 'Ble')
        self.assertEqual(field.getFilename(obj), 'eitadiacho.txt')

    def test_textfieldwithoutfilename(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Bli')
        self.assertEqual(str(field.getRaw(obj)), 'Bli')
        self.assertEqual(field.getFilename(obj), '')

    def test_textfielduploadwithoutfilename(self):
        obj = self._dummy
        file = open(join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('atextfield')
        obj.setAtextfield(file)
        file.close()
        self.assertEqual(field.getFilename(obj), 'rest1.tgz')

    def test_filefieldwithfilename(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blo', filename='beleza.jpg')
        self.assertEqual(str(obj.getAfilefield()), 'Blo')
        self.assertEqual(field.getFilename(obj), 'beleza.jpg')

    def test_filefieldwithfilename2(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blu', filename='juca.avi')
        self.assertEqual(str(obj.getAfilefield()), 'Blu')
        self.assertEqual(field.getFilename(obj), 'juca.avi')

    def test_filefieldwithoutfilename(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blao')
        self.assertEqual(str(obj.getAfilefield()), 'Blao')
        self.assertEqual(field.getFilename(obj), '')

    def test_filefielduploadwithoutfilename(self):
        obj = self._dummy
        file = open(join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('afilefield')
        obj.setAfilefield(file)
        file.close()
        self.assertEqual(field.getFilename(obj), 'rest1.tgz')


class SetFilenameTest(ArchetypesTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        file1 = open(join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        file2 = open(join(PACKAGE_HOME, 'input', 'word.doc'), 'r')
        # afilefield is the primary field
        dummy.setAfilefield(file1)
        dummy.setAnotherfilefield(file2)
        file1.close()
        file2.close()

    def testMutatorSetFilename(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        filename1 = 'rest1.tgz'
        filename2 = 'word.doc'
        self.assertEqual(field1.getFilename(obj), filename1)
        self.assertEqual(field2.getFilename(obj), filename2)

    def testBaseObjectPrimaryFieldSetFilename(self):
        obj = self._dummy
        filename1 = 'eitadiacho.mid'
        filename2 = 'ehagoraoununca.pdf'
        obj.setFilename(filename1)
        obj.setFilename(filename2, 'anotherfilefield')
        self.assertEqual(obj.getFilename(), filename1)
        self.assertEqual(obj.getFilename('afilefield'), filename1)
        self.assertEqual(obj.getFilename('anotherfilefield'), filename2)

    def testBaseObjectSetFilename(self):
        obj = self._dummy
        filename1 = 'masbahtche.avi'
        filename2 = 'guasco.mpg'
        obj.setFilename(filename1, 'afilefield')
        obj.setFilename(filename2, 'anotherfilefield')
        self.assertEqual(obj.getFilename(), filename1)
        self.assertEqual(obj.getFilename('afilefield'), filename1)
        self.assertEqual(obj.getFilename('anotherfilefield'), filename2)

    def testFieldSetFilename(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        filename1 = 'muamba.gif'
        filename2 = 'noruega.jpg'
        field1.setFilename(obj, filename1)
        field2.setFilename(obj, filename2)
        self.assertEqual(field1.getFilename(obj), filename1)
        self.assertEqual(field2.getFilename(obj), filename2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(GetFilenameTest))
    suite.addTest(makeSuite(SetFilenameTest))
    return suite

if __name__ == '__main__':
    framework()
