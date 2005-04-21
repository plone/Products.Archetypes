# -*- coding: UTF-8 -*-
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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.tests.test_classgen import ClassGenTest
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy
from Products.Archetypes.annotations import ATAnnotations
from BTrees.OOBTree import OOBTree 

from DateTime import DateTime


class AnnotationTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        self.ann = getAnnotation(self._dummy)
        
    def test_empty(self):
        ann = self.ann
        self.failUnlessEqual(bool(ann), False)
        self.failUnlessEqual(getattr(self._dummy, '__annotations__', None), None)
        
    def test_create(self):
        ann = self.ann
        ann['test'] = 'test'
        self.failUnlessEqual(bool(ann), True)
        self.failIfEqual(getattr(self._dummy, '__annotations__', None), None)
    
    def test_set(self):
        ann = self.ann
        ann['test'] = 'test1'
        self.failUnlessEqual(ann['test'], 'test1')
        ann.set('test', 'test2')
        self.failUnlessEqual(ann['test'], 'test2')
        ann.setSubkey('test', 'test3', subkey='testsub')
        self.failUnlessEqual(ann['test-testsub'], 'test3')
        self.failUnlessEqual(ann.getSubkey('test', subkey='testsub'), 'test3')
        
    def test_get(self):
        ann = self.ann
        ann['test'] = 'test1'
        self.failUnlessEqual(ann['test'], 'test1')
        self.failUnlessEqual(ann.get('test'), 'test1')
        self.failUnless(ann.has_key('test'))
        self.failUnlessEqual(ann.get('none', default='default'), 'default')
        
    def test_del(self):
        ann = self.ann
        ann['test'] = 'test1'
        del ann['test']
        self.failIf(ann.has_key('test'))

class MetadataAnnotationStorageTest(ATSiteTestCase):
    pass

class AnnotationStorageTest(ATSiteTestCase):
    pass

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(AnnotationTest))
    suite.addTest(makeSuite(MetadataAnnotationStorageTest))
    suite.addTest(makeSuite(AnnotationStorageTest))
    return suite

if __name__ == '__main__':
    framework()
