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

import sys

from Products.Archetypes.interfaces.layer import ILayer
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from ExtensionClass import Base

_marker = []

class BaseRenderer:

    def render(self, field_name, mode, widget, instance=None,
               field=None, accessor=None, **kwargs):
        if field is None:
            field = instance.Schema()[field_name]

        if accessor is None:
            accessor = field.getAccessor(instance)

        context = self.setupContext(field_name, mode, widget,
                                    instance, field, accessor, **kwargs)

        result = widget(mode, instance, context)

        del context
        return result


    def setupContext(self, field_name, mode, widget, instance, field, accessor,
                     **kwargs):
        return {}


class ArchetypesRenderer(Base, BaseRenderer):
    # XXX it says it's implementing layer but it doesn't implement the required
    # methods!
    #__implements__ = ILayer

    security = ClassSecurityInfo()
    # XXX FIXME more security

    def setupContext(self, field_name, mode, widget, instance, field, \
                     accessor, **kwargs):

        # look for the context in the stack
        frame = sys._getframe()
        context = _marker
        while context is _marker and frame is not None:
            context = frame.f_locals.get('econtext', _marker)
            frame = frame.f_back
        if context is _marker:
            raise RuntimeError, 'Context not found'

        widget = ImplicitAcquisitionWrapper(widget, instance)
        field = ImplicitAcquisitionWrapper(field, instance)
        context.setLocal('here', instance)
        context.setLocal('fieldName', field_name)
        context.setLocal('accessor', accessor)
        context.setLocal('widget', widget)
        context.setLocal('field', field)
        context.setLocal('mode', mode)

        if kwargs:
            for k,v in kwargs.items():
                context.setLocal(k, v)

        del frame
        return context

InitializeClass(ArchetypesRenderer)

