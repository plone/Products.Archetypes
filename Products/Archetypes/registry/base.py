# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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

from Interface import Interface
from Interface.IInterface import IInterface
from Products.Archetypes.interfaces.registry import IRegistry
from Products.Archetypes.interfaces.registry import IRegistryMultiplexer
from Products.Archetypes.interfaces.registry import IRegistryEntry
from Products.Archetypes.lib.utils import getDottedName


class RegistryEntry(object):
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
    >>> verifyClass(ISample, sample.cls)
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

    
    Overwriting an existing instance var isn't allowed
    >>> error = SampleEntry(Sample, __used_for__='this should fail')
    Traceback (most recent call last):
    KeyError: '__used_for__ is a forbidden key'
    
    Additional keywords must result in instance vars
    >>> sample = SampleEntry(Sample, foo='bar', egg=object)
    >>> sample.foo
    'bar'
    >>> sample.egg
    <type 'object'>
    
    Check if require is working
    >>> class SampleEntryWithName(RegistryEntry):
    ...     __used_for__ = ISample
    ...     required = ('name', )
    >>> error = SampleEntryWithName(Sample)
    Traceback (most recent call last):
    ValueError: name is required
    
    >>> sample = SampleEntryWithName(Sample, name='a sample')
    >>> sample.name
    'a sample'
    """
    __implements__ = (IRegistryEntry, )
    __used_for__ = None
    __slots__ = ('cls', '_data',)
    required = ('name', 'description')
    
    def __init__(self, cls, **kw):
        self._checkCls(cls)
        self.cls = cls
        vars = dir(self)
        for key in kw:
            if key in vars:
                raise KeyError, "%s is a forbidden key" % key
        for req in self.required:
            if req not in kw:
                raise ValueError, '%s is required' % req
        self._data = self.process(**kw)
        
    def _checkCls(self, cls):
        iface = self.__used_for__
        if not iface.isImplementedByInstancesOf(cls):
            raise ValueError, "%s does not implement %s" % (cls, getDottedName(iface))
        
    def __getattr__(self, key, default=None):
        try:
            return self._data[key]
        except KeyError:
            object.__getattr__(self, key, default)
            
    def process(self, **kw):
        return kw
    
    def beforeRegister(self, registry, key):
        pass
            
    def keys(self):
        return self._data.keys()
        
    def getModule(self):
        return getattr(self.cls, '__module__', None)

    def getDottedName(self):
        return getDottedName(self.cls)    
    

class _MetaRegistry(type):
    """Metaclass for IRegistry based classes

    The metaclass does some checks on the entryclass class var and assigns
    entry_interface according to the entry class __used_for__ class var.
    """
    def __init__(cls, name, bases, dict):
        super(_MetaRegistry, cls).__init__(name, bases, dict)
        entry_class = dict.get('_entry_class')
        if not IRegistryEntry.isImplementedByInstancesOf(entry_class):
            raise TypeError, "%s doesn't implement IRegistryEntry" % entry_class
        iface = entry_class.__used_for__
        setattr(cls, '_entry_iface', iface)

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
        
    def register(self, cls, name=None, **kw):
        if name is None:
            name = getDottedName(cls)
        ob = self._entry_class(cls, name=name **kw)
        ob.beforeRegister(registry=self, key=name)
        self[name] = ob

class RegistryMultiplexer(dict):
    """See IRegistryMultiplexer
    """
    
    __slots__ = ()
    __implements__ = IRegistryMultiplexer
    
    def __setitem__(self, key, value):
        if not IInterface.isImplementedBy(key):
            raise KeyError, 'Key must be an interface, got %s(%s)' % (key, type(key))
        if not IRegistry.isImplementedBy(value):
            raise ValueError, 'Value must be an IRegistry based instance'
        dict.__setitem__(self, key, value)
        
    def registerRegistry(self, registry):
        iface = registry._entry_iface
        self[iface] = registry
        
    def register(self, cls, **kw):
        match = None
        for iface in self.keys():
            if iface.isImplementedByInstancesOf(cls):
                if match is not None:
                    raise ValueError, 'Found more then one registry for %s:' \
                        '%s, %s' % (getDottedName(cls), getDottedName(iface),
                            getDotttedName(match))
                else:
                    match = iface
        if match is None:
            raise ValueError, 'Unable to find a registry for %s' % getDottedName(cls)
        registry = self[match]
        registry.register(cls, **kw)

mainRegistry = RegistryMultiplexer()
register = mainRegistry.register
registerRegistry = mainRegistry.registerRegistry
