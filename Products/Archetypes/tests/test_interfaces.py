#
# Skeleton Archetypes test
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

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

def className(class_):
    """ get the short class name """
    return str(class_).split('.')[-1] 


class InterfaceTest(ArchetypesTestCase):

    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        # more

    def beforeTearDown(self): 
        # more
        ArchetypesTestCase.beforeTearDown(self)

    # helper methods
    
    def _testInterfaceImplementation(self, klass, interface):
        """ tests if the klass implements the interface in the right way """
        self.failUnless(interface.isImplementedByInstancesOf(klass),
            '%s does not implement %s' % (className(klass), interface))
        try:
            verifyClass(interface, klass)
        except (BrokenImplementation, DoesNotImplement, 
          BrokenMethodImplementation), errmsg:
            self.fail('%s does not implement %s correctly: \n%s'
                % (className(klass), interface, errmsg)) 

    def _getImplements(self, klass):
        """ returns the interfaces implemented by the klass (flat)"""
        impl = getImplementsOfInstances(klass)
        if impl:
            return flattenInterfaces(impl)
        
    def _doesImplement(self, klass, lst):
        """ make shure that the klass implements at least these interfaces"""
        impl = self._getImplements(klass)
        for iface in lst:
            self.failUnless(iface in impl, '%s does not implement %s' % (className(klass), iface))

    # tests

    def testSchemaInterface(self):
        klass = Schema
        impl  = (ILayerRuntime, ILayerContainer)
        self._doesImplement(klass, impl)
        for iface in self._getImplements(klass):
            self._testInterfaceImplementation(klass, iface)

    def testOrderedBaseFolderInterface(self):
        klass = OrderedBaseFolder
        for iface in self._getImplements(klass):
            self._testInterfaceImplementation(klass, iface)

    def testMarshallerInterface(self):
        klass = Marshaller
        for iface in self._getImplements(klass):
            self._testInterfaceImplementation(klass, iface)

    def testPrimaryFieldMarshallerInterface(self):
        klass = PrimaryFieldMarshaller
        for iface in self._getImplements(klass):
            self._testInterfaceImplementation(klass, iface)

    def testRFC822MarshallerInterface(self):
        klass = RFC822Marshaller
        for iface in self._getImplements(klass):
            self._testInterfaceImplementation(klass, iface)
            
if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(InterfaceTest))
        return suite

