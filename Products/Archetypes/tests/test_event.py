"""
Unittests for the events fired by Archetypes.
"""

import os, sys
import warnings

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.interface import directlyProvides

from Testing import ZopeTestCase
from zope.app.testing import ztapi

from Products.Archetypes.atapi import BaseObject
from Products.Archetypes.interfaces import IObjectPreValidatingEvent, \
  IObjectPostValidatingEvent
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.interfaces import IBaseObject

def prehandler(ob, event):
    event.errors['foo'] = 1

def posthandler(ob, event):
    event.errors['bar'] = 1

class IObject1(IBaseObject):
    pass

class IObject2(IBaseObject):
    pass

class IObject3(IBaseObject):
    pass

class ValidationEventTests(ATSiteTestCase):
    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        ztapi.subscribe([IObject1, IObjectPreValidatingEvent],
          None, prehandler)
        ztapi.subscribe([IObject2, IObjectPostValidatingEvent],
          None, posthandler)
        ztapi.subscribe([IObject3, IObjectPreValidatingEvent],
          None, prehandler)
        ztapi.subscribe([IObject3, IObjectPostValidatingEvent],
          None, posthandler)
    
    def beforeTearDown(self):
        ATSiteTestCase.beforeTearDown(self)

    def testPreValidatingEvent(self):
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob
        
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failUnless(not errors.has_key('foo'))
        del ob
        
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob

    def testPostValidatingEvent(self):
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failUnless(not errors.has_key('bar'))
        del ob
        
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failUnless(errors['bar'])
        del ob
        
        ob = BaseObject('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(not errors.has_key('bar'))
        del ob

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ValidationEventTests))
    return suite

if __name__ == '__main__':
    framework()
