# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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
from BTrees.OOBTree import OOBTree

class TestAnnotations( ArchetypesTestCase ):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        ann = dummy.getAnnotation()
        # set an annotation to have the attribute
        ann['init'] = None
        
    def test_hasAnnotation(self):
        dummy = self._dummy
        ann = dummy.getAnnotation()
        ann['dummy'] = 'dummy'
        self.failUnless(dummy.hasAnnotation())
        self.failUnlessEqual(ann['dummy'], 'dummy')
        self.failUnlessEqual(aq_base(dummy)._at_annotations_['dummy'], 'dummy')
        
    def test_simple(self):
        dummy = self._dummy
        ann = dummy.getAnnotation()
        ann_attr = dummy._at_annotations_
        self.failIf(ann.has_key('dummy'))
        self.failUnlessEqual(ann.get('dummy', None), None)
        self.failIf(ann_attr.has_key('dummy'))
        ann['dummy'] = 1
        self.failUnless(ann.has_key('dummy'))
        self.failUnless(ann_attr.has_key('dummy'))
        self.failUnlessEqual(ann.get('dummy', None), 1)
        self.failUnless(dummy.hasAnnotation())
        self.failUnless(len(ann))
        
        del ann['dummy']
        self.failIf(ann.has_key('dummy'))
        self.failIf(ann_attr.has_key('dummy'))
        
        ann.set('dummy', 2)
        self.failUnless(ann.has_key('dummy'))
        self.failUnless(ann_attr.has_key('dummy'))
        self.failUnlessEqual(ann.get('dummy', None), 2)

    def test_stringSubkeys(self):
        dummy = self._dummy
        ann = dummy.getAnnotation()
        ann_attr = dummy._at_annotations_
        
        ann.setSubkey('foo', 1, subkeys='bar')
        self.failUnlessEqual(ann.getSubkey('foo', subkeys='bar', default=None), 1)
        self.failUnlessEqual(ann.getSubkey('foo', subkeys='egg', default=None), None)
        self.failUnlessEqual(ann.get('foo-bar', default=None), 1)
        self.failUnlessEqual(ann['foo-bar'], 1)
        self.failUnless(ann.hasSubkey('foo', subkeys='bar'))
        self.failUnless(ann.has_key('foo-bar'))
        self.failUnless(ann_attr.has_key('foo-bar'))
        
        ann.delSubkey('foo', subkeys='bar')
        self.failUnlessEqual(ann.getSubkey('foo', subkeys='bar', default=None), None)
        self.failUnlessEqual(ann.get('foo-bar',default=None), None)
        self.failIf(ann.hasSubkey('foo', subkeys='bar'))
        self.failIf(ann.has_key('foo-bar'))
        self.failIf(ann_attr.has_key('foo-bar'))

    def test_tupleSubkeys(self):
        dummy = self._dummy
        ann = dummy.getAnnotation()
        ann_attr = dummy._at_annotations_
        
        ann.setSubkey('foo', 1, subkeys=('spam', 'egg'))
        self.failUnlessEqual(ann.getSubkey('foo', subkeys=('spam', 'egg'), default=None), 1)
        self.failUnlessEqual(ann.getSubkey('foo', subkeys=('spam', 'foo'), default=None), None)
        self.failUnlessEqual(ann.get('foo-spam')['egg'], 1)
        self.failUnlessEqual(ann['foo-spam']['egg'], 1)
        self.failUnless(ann.hasSubkey('foo', subkeys='spam'))
        self.failUnless(ann.has_key('foo-spam'))
        self.failUnless(ann_attr.has_key('foo-spam'))
        self.failUnless(isinstance(ann['foo-spam'], OOBTree))
        self.failUnlessRaises(KeyError, ann.setSubkey, 'foo', 1, subkeys='spam')
        
        ann.delSubkey('foo', subkeys=('spam', 'egg'))
        self.failUnlessEqual(ann.getSubkey('foo', subkeys=('spam', 'egg'), default=None), None)
        self.failUnlessEqual(ann.get('foo-spam').get('egg'), None)
        self.failIf(ann.hasSubkey('foo', subkeys=('spam', 'egg')))
        self.failIf(ann.get('foo-spam').has_key('egg'))
        
    def test_failRight(self):
        dummy = self._dummy
        ann = dummy.getAnnotation()
        ann_attr = dummy._at_annotations_
        # failing tests TODO

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAnnotations))
    return suite

if __name__ == '__main__':
    framework()

