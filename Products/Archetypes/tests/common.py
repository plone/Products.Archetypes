#
# ArchetypesTestCase and ArcheSiteTestCase classes
#

# $Id: common.py,v 1.3.24.4 2004/05/31 17:17:38 shh42 Exp $

from Testing import ZopeTestCase

# Enable nice names for True and False from newer python versions
try:
    dummy=True
    del dummy
except NameError: # python 2.1
    True  = 1
    False = 0


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
try:
    import Interface
except ImportError:
    # Set dummy functions and exceptions for older zope versions
    def verifyClass(iface, candidate, tentative=0):
        return True
    def verifyObject(iface, candidate, tentative=0):
        return True
    def getImplementsOfInstances(object):
        return ()
    def getImplements(object):
        return ()
    def flattenInterfaces(interfaces, remove_duplicates=1):
        return ()
    class BrokenImplementation(Execption): pass
    class DoesNotImplement(Execption): pass
    class BrokenMethodImplementation(Execption): pass
else:
    from Interface.Implements import getImplementsOfInstances, \
         getImplements, flattenInterfaces
    from Interface.Verify import verifyClass, verifyObject
    from Interface.Exceptions import BrokenImplementation, DoesNotImplement
    from Interface.Exceptions import BrokenMethodImplementation
    del Interface


class TestPreconditionFailed(Exception):
    """ Some modules are missing or other preconditions have failed """
    def __init__(self, test, precondition):
        self.test = test
        self.precondition = precondition

    def __str__(self):
        return ("Some modules are missing or other preconditions "
                "for the test %s have failed: '%s' "
                % (self.test, self.precondition))


from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl import getSecurityManager

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent

from ArchetypesTestCase import ArchetypesTestCase

from ArchetypesTestCase import default_user
from ArchetypesTestCase import default_role

try:
    from ArchetypesTestCase import ArcheSiteTestCase
except ImportError, err:
    ZopeTestCase._print('%s\n' % err)
    hasArcheSiteTestCase = False
else:
    from ArchetypesTestCase import portal_name
    from ArchetypesTestCase import portal_owner
    hasArcheSiteTestCase = True

from Products.Archetypes.tests import PACKAGE_HOME

