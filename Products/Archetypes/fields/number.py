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

# common imports
from types import StringType
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storages import AttributeStorage
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.fields.base import Field
from Products.Archetypes.fields.base import ObjectField

# field specific imports
from DateTime import DateTime
from Products.Archetypes.widgets import IntegerWidget
from Products.Archetypes.widgets import DecimalWidget
from Products.Archetypes.widgets import BooleanWidget
from Products.Archetypes.widgets import CalendarWidget

__docformat__ = 'reStructuredText'

class IntegerField(ObjectField):
    """A field that stores an integer"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer',
        'size' : '10',
        'widget' : IntegerWidget,
        'default' : 0,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        if value=='':
            value=None
        elif value is not None:
            # should really blow if value is not valid
            __traceback_info__ = (self.getName(), instance, value, kwargs)
            value = int(value)

        ObjectField.set(self, instance, value, **kwargs)

registerPropertyType('default', 'integer', IntegerField)
registerField(IntegerField,
              title='Integer',
              description='Used for storing integer values')


class FloatField(ObjectField):
    """A field that stores floats"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'float',
        'default': '0.0'
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """Convert passed-in value to a float. If failure, set value to
        None."""
        if value=='':
            value=None
        elif value is not None:
            # should really blow if value is not valid
            __traceback_info__ = (self.getName(), instance, value, kwargs)
            value = float(value)

        ObjectField.set(self, instance, value, **kwargs)

registerField(FloatField,
              title='Float',
              description='Used for storing float values')


class FixedPointField(ObjectField):
    """A field for storing numerical data with fixed points"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'fixedpoint',
        'precision' : 2,
        'default' : '0.00',
        'widget' : DecimalWidget,
        'validators' : ('isDecimal'),
        })

    security  = ClassSecurityInfo()

    def _to_tuple(self, instance, value):
        """ COMMENT TO-DO """
        if not value:
            value = self.getDefault(instance)

        # XXX  :-(
        # Dezimal Point is very english. as a first hack
        # we should allow also the more contintental european comma.
        # The clean solution is to lookup:
        # * the locale settings of the zope-server, Plone, logged in user
        # * maybe the locale of the browser sending the value.
        # same should happen with the output.
        value = value.replace(',','.')

        value = value.split('.')
        __traceback_info__ = (self, value)
        if len(value) < 2:
            value = (int(value[0]), 0)
        else:
            fra = value[1][:self.precision]
            fra += '0' * (self.precision - len(fra))
            #handle leading comma e.g. .36
            if value[0]=='':
                value[0]='0'
            value = (int(value[0]), int(fra))
        return value

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        value = self._to_tuple(instance, value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        template = '%%d.%%0%dd' % self.precision
        value = ObjectField.get(self, instance, **kwargs)
        __traceback_info__ = (template, value)
        if value is None: return self.getDefault(instance)
        if type(value) in (StringType,): value = self._to_tuple(instance, value)
        return template % value

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = sum(self._to_tuple(instance, value))
        return ObjectField.validate_required(self, instance, value, errors)

registerField(FixedPointField,
              title='Fixed Point',
              description='Used for storing fixed point values')


class BooleanField(ObjectField):
    """A field that stores boolean values."""
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'widget' : BooleanWidget,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """If value is not defined or equal to 0, set field to false;
        otherwise, set to true."""
        if not value or value == '0':
            value = False
        else:
            value = True

        ObjectField.set(self, instance, value, **kwargs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return True

registerPropertyType('default', 'boolean', BooleanField)
registerField(BooleanField,
              title='Boolean',
              description='Used for storing boolean values')


class DateTimeField(ObjectField):
    """A field that stores dates and times"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """
        Check if value is an actual date/time value. If not, attempt
        to convert it to one; otherwise, set to None. Assign all
        properties passed as kwargs to object.
        """
        if not value:
            value = None
        elif not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except: #XXX bare exception
                value = None

        ObjectField.set(self, instance, value, **kwargs)

registerPropertyType('default', 'datetime', DateTimeField)
registerField(DateTimeField,
              title='Date Time',
              description='Used for storing date/time')
