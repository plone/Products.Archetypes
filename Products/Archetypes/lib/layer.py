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

from Products.Archetypes.interfaces.layer import ILayerContainer
from ExtensionClass import Base
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

class DefaultLayerContainer(Base):
    __implements__ = ILayerContainer

    security = ClassSecurityInfo()

    def __init__(self):
        self._layers = {}

    security.declarePrivate('registerLayer')
    def registerLayer(self, name, object):
        self._layers[name] = object

    security.declarePrivate('registeredLayers')
    def registeredLayers(self):
        return self._layers.items()

    security.declarePrivate('hasLayer')
    def hasLayer(self, name):
        return name in self._layers.keys()

    security.declarePrivate('getLayerImpl')
    def getLayerImpl(self, name):
        return self._layers[name]

InitializeClass(DefaultLayerContainer)

