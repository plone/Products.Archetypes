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

from Products.Archetypes.lib.utils import getDoc
from Products.Archetypes.lib.utils import findBaseTypes
from Products.Archetypes.lib.security import setSecurity
from Products.Archetypes.lib.security import mergeSecurity
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
        if isinstance(default_widget, basestring):
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

class WidgetDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description='', used_for=()):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)
        self.used_for = used_for

    def properties(self):
        from Products.Archetypes.Registry import getPropertyType
        props = []
        for k, v in self.klass._properties.items():
            prop = {}
            prop['name'] = k
            prop['type'] = getPropertyType(k, self.klass)
            prop['default'] = str(v)
            props.append(prop)

        return props

class ValidatorDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

class StorageDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)


class TypeDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description='',
                 package='', module=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)
        self.package = package
        self.module = module

    def schemata(self):
        # Build a temp instance.
        from Products.Archetypes.schema import getSchemata
        return getSchemata(self.klass('test'))

    def signature(self):
        # Build a temp instance.
        return self.klass('test').Schema().signature()

    def portal_type(self):
        return self.klass.portal_type

    def read_only(self):
        return 1

    def basetypes(self):
        return findBaseTypes(self.klass)


fieldDescriptionRegistry = Registry(FieldDescription)
availableFields = fieldDescriptionRegistry.items
def registerField(klass, **kw):
    # XXX check me high > low security order.
    #setSecurity(klass, defaultAccess=None, objectPermission=None)
    #setSecurity(klass, defaultAccess=None, objectPermission=CMFCorePermissions.View)
    setSecurity(klass, defaultAccess='allow', objectPermission=None)
    #setSecurity(klass, defaultAccess='allow', objectPermission=CMFCorePermissions.View)
    #setSecurity(klass, defaultAccess='allow', objectPermission='public')
    field = FieldDescription(klass, **kw)
    fieldDescriptionRegistry.register(field.id, field)

widgetDescriptionRegistry = Registry(WidgetDescription)
availableWidgets = widgetDescriptionRegistry.items
def registerWidget(klass, **kw):
    # XXX check me high > low security order.
    #setSecurity(klass, defaultAccess=None, objectPermission=None)
    #setSecurity(klass, defaultAccess=None, objectPermission=CMFCorePermissions.View)

    setSecurity(klass, defaultAccess='allow', objectPermission=None)
    #setSecurity(klass, defaultAccess='allow', objectPermission=CMFCorePermissions.View)
    #setSecurity(klass, defaultAccess='allow', objectPermission='public')
    widget = WidgetDescription(klass, **kw)
    widgetDescriptionRegistry.register(widget.id, widget)

storageDescriptionRegistry = Registry(StorageDescription)
availableStorages = storageDescriptionRegistry.items
def registerStorage(klass, **kw):
    setSecurity(klass, defaultAccess=None, objectPermission=None)
    storage = StorageDescription(klass, **kw)
    storageDescriptionRegistry.register(storage.id, storage)

class TypeRegistry:

    def __init__(self):
        pass

    def items(self):
        from Products.Archetypes import listTypes
        return [(className(t['klass']),
                 TypeDescription(t['klass'],
                                 title=t['name'],
                                 package=t['package'],
                                 module=t['module'],
                                 )
                 )
                 for t in listTypes()]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

    def __getitem__(self, name):
        items = self.items()
        for k, v in items:
            if k == name:
                return v
        raise KeyError, name

    def get(self, name, default=None):
        items = self.items()
        for k, v in items:
            if k == name:
                return v
        return default

class ValidatorRegistry:

    def __init__(self):
        from Products.Archetypes.validation import validationService
        self.validation = validationService

    def register(self,  name, item):
        self.validation.register(item)

    def unregister(self, name):
        self.validation.unregister(name)

    def items(self):
        return [(k, ValidatorDescription(v,
                                         title=v.title,
                                         description=v.description))
                for k, v in self.validation.items()]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

validatorDescriptionRegistry = ValidatorRegistry()
availableValidators = validatorDescriptionRegistry.items
def registerValidator(item, name=''):
    name = name or item.name
    validatorDescriptionRegistry.register(name, item)

typeDescriptionRegistry = TypeRegistry()
availableTypes = typeDescriptionRegistry.items

class PropertyMapping:

    def __init__(self):
        self._default = {}
        self._mapping = {}

    def register(self, property, type, klass=None):
        if not klass:
            map = self._default
        else:
            if not self._mapping.has_key(klass):
                self._mapping[klass] = {}
            map = self._mapping[klass]
        map[property] = type

    def getType(self, property, klass):
        value = None
        if self._mapping.has_key(klass):
            value = self._mapping[klass].get(property, None)
        return value or self._default.get(property, 'not-registered')

propertyMapping = PropertyMapping()
registerPropertyType = propertyMapping.register
getPropertyType = propertyMapping.getType
