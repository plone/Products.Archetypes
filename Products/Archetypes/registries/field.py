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

import types
import inspect

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from Globals import InitializeClass

from Products.Archetypes.lib.utils import className
from Products.Archetypes.config import DEBUG_SECURITY
from Products.Archetypes.interfaces.base import IBaseObject

from Products.Archetypes.registries.baseregistry import getDoc
from Products.Archetypes.registries.baseregistry import findBaseTypes
from Products.Archetypes.registries.baseregistry import setSecurity
from Products.Archetypes.registries.baseregistry import mergeSecurity
from Products.Archetypes.registries.baseregistry import Registry

class FieldDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, default_widget=None,
                 title='', description=''):
        self.id = className(klass)
        self.klass = klass
        default_widget = default_widget or klass._properties.get('widget', None)
        if default_widget is None:
            raise ValueError, '%r Must have a default_widget' % klass
        if type(default_widget) not in [types.StringType, types.UnicodeType]:
            default_widget = className(default_widget)
        self.default_widget = default_widget
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

    def allowed_widgets(self):
        from Products.Archetypes.Registry import availableWidgets
        widgets = []
        for k, v in availableWidgets():
            if v.used_for is None or \
               self.id in v.used_for:
                widgets.append(k)
        return widgets

    def properties(self):
        from Products.Archetypes.Registry import getPropertyType
        props = []
        for k, v in self.klass._properties.items():
            prop = {}
            prop['name'] = k
            prop['type'] = getPropertyType(k, self.klass)
            prop['default'] = v
            props.append(prop)

        return props
