"""
Unittests for the events fired by Archetypes.
"""

from zope.interface import implements, Interface, directlyProvides
from zope import component

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests import utils

from zope.publisher.browser import TestRequest

from Products.Archetypes.atapi import BaseContent

from Products.Archetypes.interfaces import IObjectPreValidation
from Products.Archetypes.interfaces import IObjectPostValidation

from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

class IObject1(Interface):
    pass

class IObject2(Interface):
    pass

class IObject3(Interface):
    pass

class Dummy(BaseContent):
    pass
utils.gen_class(Dummy)

# Subscription adapters for validation

class PreValidation(object):
    implements(IObjectPreValidation)

    def __init__(self, context):
        self.context = context

    def __call__(self, request):
        return dict(foo="Foo was invalid.")

class PostValidation(object):
    implements(IObjectPostValidation)

    def __init__(self, context):
        self.context = context

    def __call__(self, request):
        return dict(bar="Bar was invalid.")

def created_handler(ob, event):
    ob._createdCaught = True

def initialized_handler(ob, event):
    ob._initializedCaught = True

def edited_handler(ob, event):
    ob._editedCaught = True

class ValidationEventTests(ATSiteTestCase):

    def testPreValidatingEvent(self):

        # Register some subscription adapters for different types of objects
        # These will be called during validation

        component.provideSubscriptionAdapter(PreValidation, adapts=(IObject1,))
        component.provideSubscriptionAdapter(PreValidation, adapts=(IObject3,))

        # Verify that they are called only on the right type of object,
        # and that their return values are included in the error output

        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob

        ob = Dummy('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failIf(errors.has_key('foo'))
        del ob

        ob = Dummy('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(errors['foo'])
        del ob

        sm = component.getSiteManager()
        sm.unregisterSubscriptionAdapter(PreValidation, required=(IObject1,))
        sm.unregisterSubscriptionAdapter(PreValidation, required=(IObject3,))

    def testPostValidatingEvent(self):

        # This test is similar to the test for pre-validation above. The
        # difference is that the post validation works after main schema
        # validation, whilst the pre-validation works before, and may
        # short-circuit schema validation.

        component.provideSubscriptionAdapter(PostValidation, adapts=(IObject2,))
        component.provideSubscriptionAdapter(PostValidation, adapts=(IObject3,))

        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        errors = ob.validate()
        self.failIf(errors.has_key('bar'))
        del ob

        ob = Dummy('dummy')
        directlyProvides(ob, IObject2)
        errors = ob.validate()
        self.failUnless(errors['bar'])
        del ob

        ob = Dummy('dummy')
        directlyProvides(ob, IObject3)
        errors = ob.validate()
        self.failUnless(errors.has_key('bar'))
        del ob

        sm = component.getSiteManager()
        sm.unregisterSubscriptionAdapter(PostValidation, required=(IObject2,))
        sm.unregisterSubscriptionAdapter(PostValidation, required=(IObject3,))

    def testInitializedAndEditedEvent(self):

        component.provideHandler(created_handler, (IObject1, IObjectCreatedEvent,))
        component.provideHandler(initialized_handler, (IObject1, IObjectInitializedEvent,))
        component.provideHandler(edited_handler, (IObject1, IObjectEditedEvent,))

        ob = Dummy('dummy')
        directlyProvides(ob, IObject1)
        self.folder._setObject('dummy', ob)
        ob = self.folder.dummy

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

        sm = component.getSiteManager()
        sm.unregisterHandler(created_handler, (IObject1, IObjectCreatedEvent,))
        sm.unregisterHandler(initialized_handler, (IObject1, IObjectCreatedEvent,))
        sm.unregisterHandler(edited_handler, (IObject1, IObjectCreatedEvent,))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ValidationEventTests))
    return suite
