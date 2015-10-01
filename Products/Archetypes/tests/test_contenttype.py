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
"""
"""

import os

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME

# this trigger zope imports
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy
from Products.Archetypes.tests.test_classgen import default_text

from Products.Archetypes.atapi import *


class GetContentTypeTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

    def test_textfieldwithmime(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        self.assertEqual(field.getContentType(obj), 'text/x-rst')
        self.assertEqual(field.getRaw(obj), default_text)
        obj.setAtextfield('Bla', mimetype='text/x-rst')
        self.assertEqual(field.getContentType(obj), 'text/x-rst')
        self.assertEqual(field.getRaw(obj), 'Bla')

    def test_textfieldwithmime2(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Bla', mimetype='text/structured')
        self.assertEqual(field.getRaw(obj), 'Bla')
        self.assertEqual(field.getContentType(obj), 'text/structured')

    def test_textfieldwithoutmime(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Bla')
        self.assertEqual(str(field.getRaw(obj)), 'Bla')
        self.assertEqual(field.getContentType(obj), 'text/plain')

    def test_textfielduploadwithoutmime(self):
        obj = self._dummy
        file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('atextfield')
        obj.setAtextfield(file)
        file.close()
        self.assertEqual(field.getContentType(obj), 'application/x-tar')

    def test_filefieldwithmime(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Bla', mimetype='text/x-rst')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(field.getContentType(obj), 'text/x-rst')

    def test_filefieldwithmime2(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Bla', mimetype='text/structured')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(field.getContentType(obj), 'text/structured')

    def test_filefieldwithoutmime(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Bla')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')
        self.assertEqual(field.getContentType(obj), 'text/plain')

    def test_filefielduploadwithoutmime(self):
        obj = self._dummy
        file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('afilefield')
        obj.setAfilefield(file)
        file.close()
        self.assertEqual(field.getContentType(obj), 'application/x-tar')


class SetContentTypeTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        file1 = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        file2 = open(os.path.join(PACKAGE_HOME, 'input', 'word.doc'), 'r')
        # afilefield is the primary field
        dummy.setAfilefield(file1)
        dummy.setAnotherfilefield(file2)
        file1.close()
        file2.close()

    def testMutatorSetContentType(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        mimetype1 = 'application/x-tar'
        mimetype2 = 'application/msword'
        self.assertEqual(field1.getContentType(obj), mimetype1)
        self.assertEqual(field2.getContentType(obj), mimetype2)

    def testBaseObjectPrimaryFieldSetContentType(self):
        obj = self._dummy
        mimetype1 = 'application/x-gzip'
        mimetype2 = 'application/pdf'
        obj.setContentType(mimetype1)
        obj.setContentType(mimetype2, 'anotherfilefield')
        self.assertEqual(obj.getContentType(), mimetype1)
        self.assertEqual(obj.getContentType('afilefield'), mimetype1)
        self.assertEqual(obj.getContentType('anotherfilefield'), mimetype2)

    def testBaseObjectSetContentType(self):
        obj = self._dummy
        mimetype1 = 'application/x-deb'
        mimetype2 = 'application/x-compressed-tar'
        obj.setContentType(mimetype1, 'afilefield')
        obj.setContentType(mimetype2, 'anotherfilefield')
        self.assertEqual(obj.getContentType(), mimetype1)
        self.assertEqual(obj.getContentType('afilefield'), mimetype1)
        self.assertEqual(obj.getContentType('anotherfilefield'), mimetype2)

    def testFieldSetContentType(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        mimetype1 = 'image/jpeg'
        mimetype2 = 'audio/mpeg'
        field1.setContentType(obj, mimetype1)
        field2.setContentType(obj, mimetype2)
        self.assertEqual(field1.getContentType(obj), mimetype1)
        self.assertEqual(field2.getContentType(obj), mimetype2)
