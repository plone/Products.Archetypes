from Testing import ZopeTestCase

from Testing.ZopeTestCase.functional import Functional
from Products.PloneTestCase import PloneTestCase

# setup test content types
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.GenericSetup import EXTENSION, profile_registry

from Products.Archetypes.tests.utils import provideSchemaAdapters

profile_registry.registerProfile('Archetypes_sampletypes',
    'Archetypes Sample Content Types',
    'Extension profile including Archetypes sample content types',
    'profiles/sample_types',
    'Archetypes',
    EXTENSION,
    for_=IPloneSiteRoot)

# setup a Plone site
from Products.PloneTestCase.ptc import setupPloneSite
setupPloneSite(extension_profiles=['Archetypes:Archetypes',
                                   'Archetypes:Archetypes_sampletypes'
                                  ])

# Fixup zope 2.7+ configuration
from App import config
config._config.rest_input_encoding = 'ascii'
config._config.rest_output_encoding = 'ascii'
config._config.rest_header_level = 3
del config

class ATTestCase(ZopeTestCase.ZopeTestCase):
    """Simple AT test case
    """
    
    def afterSetUp(self): 
        super(ATTestCase, self).afterSetUp() 
        provideSchemaAdapters()

class ATFunctionalTestCase(Functional, ATTestCase):
    """Simple AT test case for functional tests
    """
    __implements__ = Functional.__implements__ + ATTestCase.__implements__

from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
default_user = user_name
default_role = 'Member'

__all__ = ('default_user', 'default_role', 'user_name', 'user_password',
           'ATTestCase', 'ATFunctionalTestCase', )
