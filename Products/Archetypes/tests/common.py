#
# PloneTestCase
#

# $Id: common.py,v 1.1.2.6 2003/10/21 15:22:36 tiran Exp $

# enable nice names for True and False from newer python versions
try:
    dummy=True
except NameError: # python 2.1
    True  = 1
    False = 0
    __all__Boolean = ('True', 'False',)
else:
    __all__Boolean = ()

def Xprint(s):
    """print helper
    
    print data via print is not possible, you have to use 
    ZopeTestCase._print or this function
    """
    ZopeTestCase._print(str(s)+'\n')

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from Testing import ZopeTestCase
from ArchetypesTestCase import ArchetypesTestCase
try:
    from ArcheSiteTestCase import ArcheSiteTestCase
    hasArcheSiteTestCase = True
except ImportError, err:
    Xprint(err)
    class ArcheSiteTestCase(ArchetypesTestCase): pass
    hasArcheSiteTestCase = False

# import Interface for interface testing
try:
    import Interface
except ImportError:
    # set dummy functions and exceptions for older zope versions
    def verifyClass(iface, candidate, tentative=0):
        return True
    def verifyObject(iface, candidate, tentative=0):
        return True
    def getImplementsOfInstances(object):
        return []
    def flattenInterfaces(interfaces, remove_duplicates=1):
        return []
    class BrokenImplementation(Execption): pass
    class DoesNotImplement(Execption): pass
    class BrokenMethodImplementation(Execption): pass
else:
    from Interface.Implements import getImplementsOfInstances, flattenInterfaces
    from Interface.Verify import verifyClass, verifyObject
    from Interface.Exceptions import BrokenImplementation, DoesNotImplement
    from Interface.Exceptions import BrokenMethodImplementation  

class TestPreconditionFailed(Exception):
    """ some modules are missing or other preconditions have failed """
    def __init__(self, test, precondition):
        self.test = test
        self.precondition = precondition

    def __str__(self):
        return "Some modules are missing or other preconditions for the test %s \
have failed: '%s' " % (self.test, self.precondition)

__all__ = ('ZopeTestCase', 'ArchetypesTestCase', 'ArcheSiteTestCase', 'Xprint',
           'verifyClass', 'verifyObject', 'BrokenImplementation',
           'DoesNotImplement', 'BrokenMethodImplementation', 
           'getImplementsOfInstances', 'flattenInterfaces',
           'newSecurityManager', 'noSecurityManager', 
           'TestPreconditionFailed', 'hasArcheSiteTestCase' ) \
           + __all__Boolean



