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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base

from Products.Archetypes.interfaces.marshall import IMarshall
from Products.Archetypes.interfaces.layer import ILayer


class Marshaller:
    __implements__ = IMarshall, ILayer

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def __init__(self, demarshall_hook=None, marshall_hook=None):
        self.demarshall_hook = demarshall_hook
        self.marshall_hook = marshall_hook

    def initializeInstance(self, instance, item=None, container=None):
        dm_hook = None
        m_hook = None
        if self.demarshall_hook is not None:
            dm_hook = getattr(instance, self.demarshall_hook, None)
        if self.marshall_hook is not None:
            m_hook = getattr(instance, self.marshall_hook, None)
        instance.demarshall_hook = dm_hook
        instance.marshall_hook = m_hook

    def cleanupInstance(self, instance, item=None, container=None):
        if hasattr(aq_base(instance), 'demarshall_hook'):
            delattr(instance, 'demarshall_hook')
        if hasattr(aq_base(instance), 'marshall_hook'):
            delattr(instance, 'marshall_hook')

    def demarshall(self, instance, data, **kwargs):
        raise NotImplemented

    def marshall(self, instance, **kwargs):
        raise NotImplemented

    def initializeField(self, instance, field):
        pass

    def cleanupField(self, instance, field):
        pass

InitializeClass(Marshaller)

