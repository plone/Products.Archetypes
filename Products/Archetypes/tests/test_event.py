"""
Unittests for the events fired by Archetypes.
"""

from zope.interface import Interface, directlyProvides

from Testing import ZopeTestCase
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase

from zope.app.testing import ztapi
from zope.publisher.browser import TestRequest

from Products.Archetypes.atapi import BaseContent

from Products.Archetypes.interfaces import IObjectPreValidatingEvent
from Products.Archetypes.interfaces import IObjectPostValidatingEvent
from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

class Dummy(BaseContent):
    pass

def prehandler(ob, event):
    event.errors['foo'] = 1

def posthandler(ob, event):
    event.errors['bar'] = 1
    
def createdhandler(ob, event):
    ob._createdCaught = True
    
def initializedhandler(ob, event):
    ob._initializedCaught = True
    
def editedhandler(ob, event):
    ob._editedCaught = True

class IObject1(Interface):
    pass

class IObject2(Interface):
    pass

class IObject3(Interface):
    pass

class ValidationEventTests(ATSiteTestCase):
    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        ztapi.subscribe((IObject1, IObjectPreValidatingEvent,),  None, prehandler)
        ztapi.subscribe((IObject2, IObjectPostValidatingEvent,), None, posthandler)
        ztapi.subscribe((IObject3, IObjectPreValidatingEvent,),  None, prehandler)
        ztapi.subscribe((IObject3, IObjectPostValidatingEvent,), None, posthandler)

        ztapi.subscribe((IObject1, IObjectCreatedEvent,), None, createdhandler)
        
        ztapi.subscribe((IObject1, IObjectInitializedEvent,), None, initializedhandler)
        ztapi.subscribe((IObject1, IObjectEditedEvent,), None, editedhandler)
    
    def beforeTearDown(self):
        ATSiteTestCase.beforeTearDown(self)

    def testPreValidatingEvent(self):
        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob
        
        ob = Dummy('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failUnless(not errors.has_key('foo'))
        del ob
        
        ob = Dummy('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob

    def testPostValidatingEvent(self):
        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failUnless(not errors.has_key('bar'))
        del ob
        
        ob = Dummy('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failUnless(errors['bar'])
        del ob
        
        ob = Dummy('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(not errors.has_key('bar'))
        del ob
        
    def testInitializedAndEditedEvent(self):
        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        self.folder._setObject('dummy', ob)
        
        ob._initializedCaught = False
        ob._editedCaught = False
        
        # Simulate first edit
        ob._at_creation_flag = True
        ob.processForm(REQUEST=TestRequest())
        
        self.assertEquals(True, ob._initializedCaught)
        self.assertEquals(False, ob._editedCaught)
        
        # Simulate subsequent edit
        ob.processForm(REQUEST=TestRequest())
        self.assertEquals(True, ob._editedCaught)
        

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ValidationEventTests))
    return suite
