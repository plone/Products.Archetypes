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
from Interface import Attribute

class IRegistry(Interface):
    """Registry for different classes of Archetypes
    """
    
    def __setitem__(key, value):
        """Restricted __setitem__ hook
        
        Key must be a (unicode) string
        Value must be an instance that provides IRegistryEntry and its
        __used_for__ attribute must match the registry.
        """
        
    def register(cls, name=None, **kw):
        """Registers a class with additional data
        """
        
class IRegistryMultiplexer(IRegistry):
    """Special registry that acts like a multiplexer between registries
    """
    
    def registerRegistry(registry):
        """Registers a registry
        """
        
class IRegistryEntry(Interface):
    """An interface entry
    """
    
    __used_for__ = Attribute("Interface of the class that should be stored")
    required = Attribute("List of required attributes")
    
    def process(**kw):
        """Processes the additional keywords passed to the RegistryEntry.
        
        This method can be used to check, alter or add dat to the dict **kw.
        
        It must return a dict.
        """
        
    def beforeRegister(registry, key):
        """Hook method that is called before the entry is registered.
        
        registry - The registry where the item should be registered.
        key - The key used to register the entry in.
        
        This method can be used to prevent an object from getting registered
        or to change the class before registering it.
        """
    
    def keys():
        """Return list of attributes that provide information
        """
        
    def getDottedName():
        """Return the dotted name to the class
        """
        
    def getModule():
        """Return the module where the class is defined
        """
