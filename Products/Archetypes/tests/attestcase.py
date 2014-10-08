from plone.app.testing.bbb import PloneTestCase
from Products.GenericSetup import EXTENSION, profile_registry


def setupSampleTypeProfile():
    profile_registry.registerProfile('Archetypes_sampletypes',
        'Archetypes Sample Content Types',
        'Extension profile including Archetypes sample content types',
        'profiles/sample_types',
        'Products.Archetypes',
        EXTENSION)

setupSampleTypeProfile()

class ATTestCase(PloneTestCase):
    """Simple AT test case
    """

ATFunctionalTestCase = ATTestCase
