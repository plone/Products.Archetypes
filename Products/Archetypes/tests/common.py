#
# PloneTestCase
#

# $Id: common.py,v 1.1.2.3 2003/10/20 19:01:30 tiran Exp $

from Testing import ZopeTestCase
from ArchetypesTestCase import ArchetypesTestCase
from ArcheSiteTestCase import ArcheSiteTestCase

# enable nice names for True and False from newer python versions
try:
    dummy=True
except NameError: # python 2.1
    True  = 1
    False = 0
    __all__Boolean = ('True', 'False',)
else:
    __all__Boolean = ()

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

def Xprint(s):
    """print helper
    
    print data via print is not possible, you have to use 
    ZopeTestCase._print or this function
    """
    ZopeTestCase._print(str(s))

__all__ = ('ZopeTestCase', 'ArchetypesTestCase', 'ArcheSiteTestCase', 'Xprint',
           'verifyClass', 'verifyObject', 'BrokenImplementation',
           'DoesNotImplement', 'BrokenMethodImplementation', 
           'getImplementsOfInstances', 'flattenInterfaces') \
           + __all__Boolean



