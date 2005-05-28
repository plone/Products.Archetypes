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
"""Widget registry
"""

__author__ = 'Christian Heimes'

from Products.Archetypes.registry.base import registerRegistry
from Products.Archetypes.registry.base import Registry
from Products.Archetypes.registry.base import RegistryEntry
from Products.Archetypes.interfaces.widget import IWidget
from Products.Archetypes.lib.security import setSecurity

class WidgetEntry(RegistryEntry):
    __used_for__ = IWidget

    def beforeRegister(self, registry, key):
        """Hook
        
        * Set security
        """
        # set security
        klass = self['klass']
        setSecurity(klass, defaultAccess='allow', objectPermission=None)

class WidgetRegistry(Registry):
    _entry_class = WidgetEntry

_widgetRegistry = WidgetRegistry()
registerRegistry(_widgetRegistry)
