#
# Skeleton Archetypes test
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from types import TupleType

from Products.Archetypes.interfaces.base import *
from Products.Archetypes.interfaces.field import *
from Products.Archetypes.interfaces.layer import *
from Products.Archetypes.interfaces.marshall import *
from Products.Archetypes.interfaces.metadata import *
from Products.Archetypes.interfaces.orderedfolder import *
from Products.Archetypes.interfaces.referenceable import *
from Products.Archetypes.interfaces.storage import *

from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.BaseContent import BaseContent, I18NBaseContent
from Products.Archetypes.BaseFolder import BaseFolder, I18NBaseFolder
from Products.Archetypes.BaseUnit import newBaseUnit, oldBaseUnit
from Products.Archetypes import Field # use __all__ field
from Products.Archetypes.Marshall import Marshaller, PrimaryFieldMarshaller, \
    RFC822Marshaller
from Products.Archetypes.OrderedBaseFolder import OrderedBaseFolder
from Products.Archetypes.Schema import Schema
from Products.Archetypes.SQLStorage import BaseSQLStorage, GadflySQLStorage, \
    MySQLSQLStorage, PostgreSQLStorage
from Products.Archetypes.Storage import Storage, ReadOnlyStorage, \
    StorageLayer, AttributeStorage, ObjectManagedStorage, MetadataStorage
from Products.Archetypes.Validators import DateValidator

def className(klass):
    """ get the short class name """
    return str(klass).split('.')[-1].split(' ')[0]

# list of tests
tests = []

class InterfaceTest(ArchetypesTestCase):
    """general interface testing class
    
    klass - the class object to test
    forcedImpl - a list of interface class objects that the class klass 
        *must* implement to fullfil this test
    
    This test class doesn't implement a test* method so you have to provide
    a test method in your implementation. See above for two examples. One
    example uses the special magic of setattr::
    
        setattr(MyClass, MyMethodName, lambda self: self._testStuff())
        
    """

    klass = None    # test this class
    forcedImpl = () # class must implement this tuple of interfaces

    def _testInterfaceImplementation(self, klass, interface):
        """ tests if the klass implements the interface in the right way """
        # is the class really implemented by the given interface?
        self.failUnless(interface.isImplementedByInstancesOf(klass),
            '%s does not implement %s' % (className(klass), className(interface)))
        # verify if the implementation is correct
        try:
            verifyClass(interface, klass)
        except (BrokenImplementation, DoesNotImplement, 
          BrokenMethodImplementation), errmsg:
            self.fail('%s does not implement %s correctly: \n%s'
                % (className(klass), className(interface), errmsg)) 

    def _getImplements(self, klass):
        """ returns the interfaces implemented by the klass (flat)"""
        impl = getImplementsOfInstances(klass)
        if type(impl) is not TupleType:
             impl = (impl,)
        if impl:
            return flattenInterfaces(impl)
        
    def _doesImplement(self, klass, interfaces):
        """ make shure that the klass implements at least these interfaces"""
        if type(interfaces) is not TupleType:
            interfaces = (interfaces)
        impl = self._getImplements(klass)
        for iface in interfaces:
            self.failUnless(iface in impl, '%s does not implement %s' % (className(klass), className(iface)))

    def _testStuff(self):
        """ test self.klass """
        if self.forcedImpl:
           self._doesImplement(self.klass, self.forcedImpl)
        for iface in self._getImplements(self.klass):
           self._testInterfaceImplementation(self.klass, iface)

###############################################################################
###                         testing starts here                             ###
###############################################################################

class FieldInterfaceTest(InterfaceTest):
    """ test all field classes from Field.Field.__all__"""
    
    klass = Field.Field # not used but set to class Field
    forcedImpl = ()

    def testFieldInterface(self):
        for fieldname in Field.__all__:
            klass = getattr(Field, fieldname)
            self._doesImplement(klass, self.forcedImpl)
            for iface in self._getImplements(klass):
                self._testInterfaceImplementation(klass, iface)

tests.append(FieldInterfaceTest)

# format: (class object, (list interface objects))
testClasses = [
    (BaseObject, ()),
    (BaseContent, ()), (I18NBaseContent, ()), 
    (BaseFolder, ()), (I18NBaseFolder, ()), 
    (newBaseUnit, ()), (oldBaseUnit, ()), 
    (Marshaller, ()), (PrimaryFieldMarshaller, ()), (RFC822Marshaller, ()), 
    (OrderedBaseFolder, ()), 
    (Schema, ()), 
    (Storage, ()), (ReadOnlyStorage, ()), (StorageLayer, ()), 
        (AttributeStorage, ()), (ObjectManagedStorage, ()),
        (MetadataStorage, ()),
    (BaseSQLStorage, ()), (GadflySQLStorage, ()), (MySQLSQLStorage, ()),
        (PostgreSQLStorage, ()), 
    (DateValidator, ()), 
]
 
for testClass in testClasses:
    klass, forcedImpl = testClass
    name = className(klass)
    funcName = 'test%sInterface' % name
    
    class KlassInterfaceTest(InterfaceTest):
        """ implementation for %s """ % name
        klass      = klass
        forcedImpl = forcedImpl
    
    # add the testing method to the class to get a nice name
    setattr(KlassInterfaceTest, funcName, lambda self: self._testStuff())  
    tests.append(KlassInterfaceTest)
            

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        for test in tests:
            suite.addTest(unittest.makeSuite(test))
        return suite