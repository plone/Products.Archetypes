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
from Products.Archetypes.widgets import ComputedWidget
from Products.Archetypes.storages import ReadOnlyStorage

__docformat__ = 'reStructuredText'

class ComputedField(ObjectField):
    """A field that stores a read-only computation"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'computed',
        'expression': None,
        'widget' : ComputedWidget,
        'mode' : 'r',
        'storage': ReadOnlyStorage(),
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, *ignored, **kwargs):
        pass

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        """Return computed value"""
        return eval(self.expression, {'context': instance, 'here' : instance})

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 0

registerField(ComputedField,
              title='Computed',
              description=('Read-only field, which value is '
                           'computed from a python expression'))
