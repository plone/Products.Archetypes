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

from Interface import Interface

class ILayer(Interface):
    """Layering support
    """


    def initializeInstance(instance, item=None, container=None):
        """Optionally called to initialize a layer for an entire
        instance
        """

    def initializeField(instance, field):
        """Optionally called to initialize a layer for a given field
        """

    def cleanupField(instance, field):
        """Optionally called to cleanup a layer for a given field
        """

    def cleanupInstance(instance, item=None, container=None):
        """Optionally called to cleanup a layer for an entire
        instance
        """

class ILayerContainer(Interface):
    """An object that contains layers and can use/manipulate them"""

    def registerLayer(name, object):
        """Register an object as providing a new layer under a given
        name
        """

    def registeredLayers():
        """Provides a list of (name, object) layer pairs
        """

    def hasLayer(name):
        """Boolean indicating if the layer is implemented on the
        object
        """

    def getLayerImpl(name):
        """Return an object implementing this layer
        """

class ILayerRuntime(Interface):
    """ Layer Runtime """

    def initializeLayers(instance, item=None, container=None):
        """Optionally process all layers attempting their
        initializeInstance and initializeField methods if they exist
        """

    def cleanupLayers(instance, item=None, container=None):
        """Optionally process all layers attempting their
        cleanupInstance and cleanupField methods if they exist.
        """

