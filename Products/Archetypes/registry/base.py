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
"""
"""

__author__ = 'Christian Heimes'

import sys

from Interface import Interface
#from Interface.IInterface import IInterface
from Products.Archetypes.interfaces.registry import IRegistry
from Products.Archetypes.interfaces.registry import IRegistryMultiplexer
from Products.Archetypes.interfaces.registry import IRegistryEntry
from Products.Archetypes.lib.utils import getDottedName

_marker = object()

class RegistryEntry(dict):
    """See IRegistryEntry

    >>> class ISample(Interface): pass
    >>> class Sample(object):
    ...     __implements__ = ISample
    >>> class SampleEntry(RegistryEntry):
    ...     __used_for__ = ISample
    ...     required = ()
    >>> sample = SampleEntry(Sample)

    Check the interfaces
    >>> from Interface.Verify import verifyClass
    >>> verifyClass(IRegistryEntry, SampleEntry)
    1
    >>> verifyClass(ISample, sample['klass'])
    1

    Check if adding a class which doesn't implement our interface does fail
    >>> error = SampleEntry(object)
    Traceback (most recent call last):
    ValueError: <type 'object'> does not implement Products.Archetypes.registry.base.ISample

    Interfaces must match
    >>> class IOther(Interface): pass
    >>> class Other(object):
    ...     __implements__ = IOther
    >>> error = SampleEntry(Other)
    Traceback (most recent call last):
    ValueError: <class 'Products.Archetypes.registry.base.Other'> does not implement Products.Archetypes.registry.base.ISample


    Additional keywords must result in instance vars
    >>> sample = SampleEntry(Sample, foo='bar', egg=object)
    >>> sample['foo']
    'bar'
    >>> sample['egg']
    <type 'object'>

    Check if require is working
    >>> class SampleEntryWithName(RegistryEntry):
    ...     __used_for__ = ISample
    ...     required = ('name', )
    >>> error = SampleEntryWithName(Sample)
    Traceback (most recent call last):
    ValueError: name is required

    >>> sample = SampleEntryWithName(Sample, name='a sample')
    >>> sample['name']
    'a sample'
    """
    __implements__ = (IRegistryEntry, )
    __used_for__ = None
    __slots__ = ()
    required = ('name', 'description', 'registry_key', )
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, **kw):
        self._checkClass(klass)
        self['klass'] = klass
        kw = self.process(**kw)
        for req in self.required:
            if req not in kw:
                raise ValueError, '%s is required' % req
        self.update(kw)

    def __guarded_getattr__(self, name):
        print self, name
        return getattr(self, name)

    def _checkClass(self, klass):
        """Chech if the class matches the constrains for the entry
        """
        iface = self.__used_for__
        if not iface.isImplementedByInstancesOf(klass):
            raise ValueError, "%s does not implement %s" % (klass, getDottedName(iface))

    def process(self, **kw):
        """Process the keyword arguments
        
        May be used to add additional data or check the data
        """
        return kw

    def beforeRegister(self, registry, key):
        """Called before the entry is registered
        
        registry is the registry instance to which the entry is added
        key is the key under which the entry is registered
        """
        pass

    def getModule(self):
        """Return the module in which the class is defined
        """
        module_name = self['klass'].__module__
        return sys.modules[module_name]

    def getDottedName(self):
        """Return the dotted name of the class
        """
        return getDottedName(self['klass'])


class _MetaRegistry(type):
    """Metaclass for IRegistry based classes

    The metaclass does some checks on the entryclass class var and assigns
    entry_interface according to the entry class __used_for__ class var.
    """
    def __init__(klass, name, bases, dict):
        super(_MetaRegistry, klass).__init__(name, bases, dict)
        entry_class = dict.get('_entry_class')
        if not IRegistryEntry.isImplementedByInstancesOf(entry_class):
            raise TypeError, "%s doesn't implement IRegistryEntry" % entry_class
        iface = entry_class.__used_for__
        setattr(klass, '_entry_iface', iface)

class Registry(dict):
    """See IRegistry

    Setup a sample registry with sample entry
    >>> class ISample(Interface): pass
    >>> class Sample(object):
    ...     __implements__ = ISample
    >>> class SampleEntry(RegistryEntry):
    ...     __used_for__ = ISample
    ...     required = ()
    >>> class SampleRegistry(Registry):
    ...     _entry_class = SampleEntry
    >>> sr = SampleRegistry()

    Check the interfaces
    >>> from Interface.Verify import verifyObject
    >>> verifyObject(IRegistry, sr)
    1

    Check metaclass
    >>> sr._entry_iface is ISample
    True

    Check __setitem__ restrictions
    >>> sr[object] = SampleEntry(Sample)
    Traceback (most recent call last):
    KeyError: 'Registry key must be a string'
    >>> sr['foo'] = object
    Traceback (most recent call last):
    ValueError: <type 'object'> doesn't provide IRegistryEntry
    >>> class IOther(Interface): pass
    >>> class Other(object):
    ...     __implements__ = IOther
    >>> class OtherEntry(RegistryEntry):
    ...     __used_for__ = IOther
    ...     required = ()
    >>> sr['foo'] = OtherEntry(Other)
    Traceback (most recent call last):
    ValueError: Products.Archetypes.registry.base.OtherEntry implements Products.Archetypes.registry.base.IOther instead of Products.Archetypes.registry.base.ISample

    """
    __slots__ = ('entry_class', '_entry_iface') # save memory
    __metaclass__ = _MetaRegistry
    __implements__ = IRegistry
    _entry_class = RegistryEntry

    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise KeyError, 'Registry key must be a string'
        if not IRegistryEntry.isImplementedBy(value):
            raise ValueError, "%s doesn't provide IRegistryEntry" % value
        if not value.__used_for__ is self._entry_iface:
            raise ValueError, "%s implements %s instead of %s" % \
                (getDottedName(value), getDottedName(value.__used_for__),
                 getDottedName(self._entry_iface))
        dict.__setitem__(self, key, value)

    def register(self, klass, key=None, **kw):
        """Registers a class
        
        The key is autogenerated when not provided. Instead of the class an
        entry that contains the class and additional data is added to the 
        registry.
        """
        key = self._createKey(klass, key, **kw)
        ob = self._entry_class(klass, registry_key=key, **kw)
        ob.beforeRegister(registry=self, key=key)
        self[key] = ob
        
    def _createKey(self, klass, key, **kw):
        """Hook to auto-create a key
        """
        if key is None:
            key = getDottedName(klass)

class RegistryMultiplexer(dict):
    """See IRegistryMultiplexer
    """

    __slots__ = ()
    __implements__ = IRegistryMultiplexer

    def __setitem__(self, key, value):
        #if not IInterface.isImplementedBy(key):
        #    raise KeyError, 'Key must be an interface, got %s(%s)' % (key, type(key))
        if not IRegistry.isImplementedBy(value):
            raise ValueError, 'Value must be an IRegistry based instance'
        dict.__setitem__(self, key, value)

    def registerRegistry(self, registry):
        iface = registry._entry_iface
        self[iface] = registry

    def register(self, klass, **kw):
        match = None
        for iface in self.keys():
            if iface.isImplementedByInstancesOf(klass):
                if match is not None:
                    raise ValueError, 'Found more then one registry for %s:' \
                        '%s, %s' % (getDottedName(klass), getDottedName(iface),
                            getDotttedName(match))
                else:
                    match = iface
        if match is None:
            raise ValueError, 'Unable to find a registry for %s' % getDottedName(klass)
        registry = self[match]
        registry.register(klass, **kw)

mainRegistry = RegistryMultiplexer()
registerComponent = mainRegistry.register
registerRegistry = mainRegistry.registerRegistry
getRegistry = mainRegistry.__getitem__
