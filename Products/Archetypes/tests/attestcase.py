#
# ArchetypesTestCase
#
# $Id: ArchetypesTestCase.py 3433 2005-01-17 00:31:49Z tiran $

from Testing import ZopeTestCase
from Testing.ZopeTestCase.functional import Functional

DEPS = ('CMFCore', 'CMFDefault', 'CMFCalendar', 'CMFTopic',
        'DCWorkflow', 'CMFActionIcons', 'CMFQuickInstallerTool',
        'CMFFormController',  'ZCTextIndex', 'TextIndexNG2',
        'MailHost', 'PageTemplates', 'PythonScripts', 'ExternalMethod',
        )
DEPS_PLONE = ('GroupUserFolder', 'SecureMailHost', 'CMFPlone',)
DEPS_OWN = ('MimetypesRegistry', 'PortalTransforms', 'Archetypes',
            'ArchetypesTestUpdateSchema',)

default_user = ZopeTestCase.user_name
default_role = 'Member'

# install products
for product in DEPS + DEPS_OWN:
    ZopeTestCase.installProduct(product)

# Fixup zope 2.7+ configuration
try:
    from App import config
except ImportError:
    pass
else:
    config._config.rest_input_encoding = 'ascii'
    config._config.rest_output_encoding = 'ascii'
    config._config.rest_header_level = 3
    del config

class ATTestCase(ZopeTestCase.ZopeTestCase):
    """Simple AT test case
    """

class ATFunctionalTestCase(Functional, ATTestCase):
    """Simple AT test case for functional tests
    """
    __implements__ = Functional.__implements__ + ATTestCase.__implements__ 
    
__all__ = ('default_user', 'default_role', 'ATTestCase',
           'ATFunctionalTestCase', )
