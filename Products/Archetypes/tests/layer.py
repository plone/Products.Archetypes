from Testing.ZopeTestCase.layer import ZopeLite

from zope.testing.cleanup import cleanUp

from Products.CMFCore.testing import FunctionalZCMLLayer
from Products.CMFTestCase import layer as cmf_layer

# BBB Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class ZCML(FunctionalZCMLLayer):

    def setUp(cls):
        '''Sets up the CA.'''
        import Products.CMFDefault
        zcml.load_config('configure.zcml', Products.CMFDefault)

        import Products.CMFCalendar
        zcml.load_config('configure.zcml', Products.CMFCalendar)

        import Products.DCWorkflow
        zcml.load_config('configure.zcml', Products.DCWorkflow)

        import Products.Archetypes
        zcml.load_config('configure.zcml', Products.Archetypes)

        import Products.PlacelessTranslationService
        zcml.load_config('configure.zcml', Products.PlacelessTranslationService)

        import plone.uuid
        zcml.load_config('configure.zcml', plone.uuid)

    setUp = classmethod(setUp)

    def tearDown(cls):
        '''Cleans up the CA.'''
        cleanUp()
    tearDown = classmethod(tearDown)


class ArchetypesSite(ZCML):

    def setUp(cls):
        '''Sets up the CA.'''
        for func, args, kw in cmf_layer._deferred_setup:
            func(*args, **kw)

    setUp = classmethod(setUp)

    def tearDown(cls):
        '''Cleans up the CA.'''
        for func, args, kw in cmf_layer._deferred_cleanup:
            func(*args, **kw)

        # cleanUp()
    tearDown = classmethod(tearDown)
