from Testing import ZopeTestCase
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from Testing.ZopeTestCase.functional import Functional

from Products.CMFTestCase import CMFTestCase
from Products.CMFTestCase.ctc import setupCMFSite
from Products.CMFTestCase.layer import onsetup
from Products.GenericSetup import EXTENSION, profile_registry

from Products.Archetypes.tests.layer import ZCML

default_user = user_name
default_role = 'Member'

@onsetup
def setupSampleTypeProfile():
    profile_registry.registerProfile('Archetypes_sampletypes',
        'Archetypes Sample Content Types',
        'Extension profile including Archetypes sample content types',
        'profiles/sample_types',
        'Products.Archetypes',
        EXTENSION)

# setup a CMF site
ZopeTestCase.installProduct('PythonScripts')
ZopeTestCase.installProduct('SiteErrorLog')
ZopeTestCase.installProduct('CMFFormController')
ZopeTestCase.installProduct('CMFQuickInstallerTool')
ZopeTestCase.installProduct('MimetypesRegistry')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('Archetypes')

setupSampleTypeProfile()
setupCMFSite(
    extension_profiles=['Products.CMFFormController:CMFFormController',
                        'Products.CMFQuickInstallerTool:CMFQuickInstallerTool',
                        'Products.MimetypesRegistry:MimetypesRegistry',
                        'Products.PortalTransforms:PortalTransforms',
                        'Products.Archetypes:Archetypes',
                        'Products.Archetypes:Archetypes_sampletypes'])

class ATTestCase(ZopeTestCase.ZopeTestCase):
    """Simple AT test case
    """
    layer = ZCML

class ATFunctionalTestCase(Functional, ATTestCase):
    """Simple AT test case for functional tests
    """
    layer = ZCML
