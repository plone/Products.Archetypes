# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase

from Interface.Implements import getImplementsOfInstances
from Interface.Implements import getImplements
from Interface.Implements import flattenInterfaces
from Interface.Verify import verifyClass, verifyObject
from Interface.Exceptions import BrokenImplementation
from Interface.Exceptions import DoesNotImplement
from Interface.Exceptions import BrokenMethodImplementation

from Products.Archetypes.interfaces.base import *
from Products.Archetypes.interfaces.field import *
from Products.Archetypes.interfaces.layer import *
from Products.Archetypes.interfaces.marshall import *
from Products.Archetypes.interfaces.metadata import *
from Products.Archetypes.interfaces.orderedfolder import *
from Products.Archetypes.interfaces.referenceable import *
from Products.Archetypes.interfaces.storage import *

from Products.Archetypes.base.baseobject import BaseObject
from Products.Archetypes.base.basecontent import BaseContent
from Products.Archetypes.base.basefolder import BaseFolder
from Products.Archetypes.lib.baseunit import BaseUnit
from Products.Archetypes import field as at_fields # use __all__ field
from Products.Archetypes.marshall import Marshaller, PrimaryFieldMarshaller, \
    RFC822Marshaller
from Products.Archetypes.base.baseorderedfolder import OrderedBaseFolder
from Products.Archetypes.schema import Schema
from Products.Archetypes.storage.sql.storage import BaseSQLStorage, GadflySQLStorage, \
    MySQLSQLStorage, PostgreSQLStorage
from Products.Archetypes.storage import Storage, ReadOnlyStorage, \
    StorageLayer, AttributeStorage, ObjectManagedStorage, MetadataStorage
from Products.Archetypes.base.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.atapi import registerType

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
        if not isinstance(impl, tuple):
            impl = (impl,)
        if impl:
            return flattenInterfaces(impl)

    def getImplementsOf(self, instance):
        """ returns the interfaces implemented by the instance (flat)"""
        impl = getImplements(instance)
        if not isinstance(impl, tuple):
            impl = (impl,)
        if impl:
            return flattenInterfaces(impl)

    def doesImplementByInstanceOf(self, klass, interfaces):
        """ make shure that the klass implements at least these interfaces"""
        if not isinstance(interfaces, tuple):
            interfaces = (interfaces)
        impl = self.getImplementsOfInstanceOf(klass)
        for interface in interfaces:
            self.failUnless(interface in impl, 'The class %s does not implement %s' % (className(klass), className(interface)))

    def doesImplementBy(self, instance, interfaces):
        """ make shure that the klass implements at least these interfaces"""
        if not isinstance(interfaces, tuple):
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

    klass = at_fields.Field # not used but set to class Field
    forcedImpl = ()

    def testFieldInterface(self):
        from Products.Archetypes.registries import availableFields
        for fieldname, fielddescription in availableFields():
            klass = fielddescription.klass
            instance = klass()
            self.doesImplementByInstanceOf(klass, self.forcedImpl)
            for iface in self.getImplementsOf(instance):
                self.interfaceImplementedBy(instance, iface)

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
#class EM(ExtensibleMetadata): pass
#registerType(EM, PROJECTNAME)
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
