#
# ArchetypesTestCase and ArcheSiteTestCase classes
#

# $Id$

from Testing import ZopeTestCase

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

# Import Interface for interface testing


from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl import getSecurityManager

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent

from Products.Archetypes.tests.ArchetypesTestCase import ArchetypesTestCase
from Products.Archetypes.tests.ArchetypesTestCase import default_user
from Products.Archetypes.tests.ArchetypesTestCase import default_role
from Products.Archetypes.tests.ArchetypesTestCase import ArcheSiteTestCase
from Products.Archetypes.tests.ArchetypesTestCase import portal_name
from Products.Archetypes.tests.ArchetypesTestCase import portal_owner

from Products.Archetypes.tests import PACKAGE_HOME
from Products.Archetypes.atapi import registerType, process_types, listTypes
from Products.Archetypes.config import PKG_NAME

def gen_class(klass, schema=None):
    """generats and registers the klass
    """
    if schema is not None:
        klass.schema = schema.copy()
    registerType(klass)
    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)

def mkDummyInContext(klass, oid, context, schema=None):
    gen_class(klass, schema)
    dummy = klass(oid=oid).__of__(context)
    setattr(context, oid, dummy)
    dummy.initializeArchetype()
    return dummy

