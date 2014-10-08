from zope.testing.cleanup import cleanUp
from plone.app.testing import PloneSandboxLayer


class ArchettypesFixture(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        '''Sets up the CA.'''
        import Products.DCWorkflow
        self.loadZCML(package=Products.DCWorkflow)

        import Products.Archetypes
        self.loadZCML(package=Products.Archetypes)

        import Products.PlacelessTranslationService
        self.loadZCML(package=Products.PlacelessTranslationService)

        import plone.uuid
        self.loadZCML(package=plone.uuid)

    def tearDownZope(cls):
        '''Cleans up the CA.'''
        # XXX needed?
        cleanUp()

AT_FIXTURE = ArchettypesFixture()
