from plone.app.testing import bbb
from plone.app.testing import FunctionalTesting, applyProfile
from Products.GenericSetup import EXTENSION, profile_registry


def setupSampleTypeProfile():
    profile_registry.registerProfile('Archetypes_sampletypes',
        'Archetypes Sample Content Types',
        'Extension profile including Archetypes sample content types',
        'profiles/sample_types',
        'Products.Archetypes',
        EXTENSION)

class ATTestCaseFixture(bbb.PloneTestCaseFixture):

    defaultBases = (bbb.PTC_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        print("zope")
        setupSampleTypeProfile()

    def setUpPloneSite(self, portal):
        print("plone")
        applyProfile(portal, 'Products.Archetypes:Archetypes_sampletypes')

AT_FIXTURE = ATTestCaseFixture()
AT_FUNCTIONAL_TESTING = FunctionalTesting(bases=(AT_FIXTURE,),
                                          name='Archetypes:Functional')

class ATTestCase(bbb.PloneTestCase):
    """Simple AT test case
    """

    layer = AT_FUNCTIONAL_TESTING

ATFunctionalTestCase = ATTestCase
