import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.Archetypes.tests.common import *

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
from Products.Archetypes.BaseContent import BaseContent
from Products.Archetypes.BaseFolder import BaseFolder
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes import Field # use __all__ field
from Products.Archetypes.Marshall import Marshaller, PrimaryFieldMarshaller, \
    RFC822Marshaller
from Products.Archetypes.OrderedBaseFolder import OrderedBaseFolder
from Products.Archetypes.Schema import Schema
from Products.Archetypes.SQLStorage import BaseSQLStorage, GadflySQLStorage, \
    MySQLSQLStorage, PostgreSQLStorage
from Products.Archetypes.Storage import Storage, ReadOnlyStorage, \
    StorageLayer, AttributeStorage, ObjectManagedStorage, MetadataStorage
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.public import registerType

def className(klass):
    """ get the short class name """
    # remove <>
    name = str(klass)[1:-1]
    return name.split('.')[-1].split(' ')[0]

# list of tests
tests = []

class InterfaceTest(ZopeTestCase.ZopeTestCase):
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
    instance = None # test this instance
    forcedImpl = () # class must implement this tuple of interfaces

    def interfaceImplementedByInstanceOf(self, klass, interface):
        """ tests if the klass implements the interface in the right way """
        # is the class really implemented by the given interface?
        self.failUnless(interface.isImplementedByInstancesOf(klass),
            'The class %s does not implement %s' % (className(klass), className(interface)))
        # verify if the implementation is correct
        try:
            verifyClass(interface, klass)
        except (BrokenImplementation, DoesNotImplement,
          BrokenMethodImplementation), errmsg:
            self.fail('The class %s does not implement %s correctly: \n%s'
                % (className(klass), className(interface), errmsg))

    def interfaceImplementedBy(self, instance, interface):
        """ tests if the instance implements the interface in the right way """
        # is the class really implemented by the given interface?
        self.failUnless(interface.isImplementedBy(instance),
            'The instance of %s does not implement %s' % (className(instance), className(interface)))
        # verify if the implementation is correct
        try:
            verifyObject(interface, instance)
        except (BrokenImplementation, DoesNotImplement,
          BrokenMethodImplementation), errmsg:
            self.fail('The instance of %s does not implement %s correctly: \n%s'
                % (className(instance), className(interface), errmsg))

    def getImplementsOfInstanceOf(self, klass):
        """ returns the interfaces implemented by the klass (flat)"""
        impl = getImplementsOfInstances(klass)
        if type(impl) is not TupleType:
            impl = (impl,)
        if impl:
            return flattenInterfaces(impl)

    def getImplementsOf(self, instance):
        """ returns the interfaces implemented by the instance (flat)"""
        impl = getImplements(instance)
        if type(impl) is not TupleType:
            impl = (impl,)
        if impl:
            return flattenInterfaces(impl)

    def doesImplementByInstanceOf(self, klass, interfaces):
        """ make shure that the klass implements at least these interfaces"""
        if type(interfaces) is not TupleType:
            interfaces = (interfaces)
        impl = self.getImplementsOfInstanceOf(klass)
        for interface in interfaces:
            self.failUnless(interface in impl, 'The class %s does not implement %s' % (className(klass), className(interface)))

    def doesImplementBy(self, instance, interfaces):
        """ make shure that the klass implements at least these interfaces"""
        if type(interfaces) is not TupleType:
            interfaces = (interfaces)
        impl = self.getImplementsOf(instance)
        for interface in interfaces:
            self.failUnless(interface in impl, 'The instance of %s does not implement %s' % (className(instance), className(interface)))

    def _testStuff(self):
        """ test self.klass and self.instance """
        if self.klass:
            if self.forcedImpl:
                self.doesImplementByInstanceOf(self.klass, self.forcedImpl)
            for iface in self.getImplementsOfInstanceOf(self.klass):
                self.interfaceImplementedByInstanceOf(self.klass, iface)
        if self.instance:
            if self.forcedImpl:
                self.doesImplementBy(self.instance, self.forcedImpl)
            for iface in self.getImplementsOf(self.instance):
                self.interfaceImplementedBy(self.instance, iface)

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
            self.doesImplementByInstanceOf(klass, self.forcedImpl)
            for iface in self.getImplementsOfInstanceOf(klass):
                self.interfaceImplementedByInstanceOf(klass, iface)

tests.append(FieldInterfaceTest)

# format: (class object, (list interface objects))
testClasses = [
    (BaseObject, ()),
    (BaseUnit, ()),
    (Marshaller, ()), (PrimaryFieldMarshaller, ()), (RFC822Marshaller, ()),
    (Schema, ()),
    (Storage, ()), (ReadOnlyStorage, ()), (StorageLayer, ()),
        (AttributeStorage, ()), (ObjectManagedStorage, ()),
        (MetadataStorage, ()),
    (BaseSQLStorage, ()), (GadflySQLStorage, ()), (MySQLSQLStorage, ()),
        (PostgreSQLStorage, ()),
]

PROJECTNAME = 'Archetypes.tests'
class EM(ExtensibleMetadata): pass
registerType(EM, PROJECTNAME)
class BC(BaseContent): pass
registerType(BC, PROJECTNAME)
class BF(BaseFolder): pass
registerType(BF, PROJECTNAME)
class OBF(OrderedBaseFolder): pass
registerType(OBF, PROJECTNAME)

# format: (instance object, (list interface objects))
# take care: you must provide an instance, not a class!
testInstances = [
    # (EM(), ()), XXX See comment on ExtensibleMetadata
    (BC('test'), ()),
    (BF('test'), ()),
    (OBF('test'), ()),
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

for testInstance in testInstances:
    instance, forcedImpl = testInstance
    name = className(instance)
    funcName = 'test%sInterface' % name

    class InstanceInterfaceTest(InterfaceTest):
        """ implementation for %s """ % name
        instance   = instance
        forcedImpl = forcedImpl

    # add the testing method to the class to get a nice name
    setattr(InstanceInterfaceTest, funcName, lambda self: self._testStuff())
    tests.append(InstanceInterfaceTest)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()
