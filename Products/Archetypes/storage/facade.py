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

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.storage import StorageLayer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.field import encode

from AccessControl import ClassSecurityInfo
from Products.Archetypes.registries import registerStorage

class FacadeMetadataStorage(StorageLayer):
    """A Facade Storage which delegates to
    CMFMetadata's Metadata Tool for actually
    storing the metadata values
    """

    security = ClassSecurityInfo()

    __implements__ = (IStorage, ILayer)

    def __init__(self, metadata_set):
        self.metadata_set = metadata_set

    security.declarePrivate('getTool')
    def getTool(self, instance):
        return getToolByName(instance, 'portal_metadata')

    security.declarePrivate('initializeInstance')
    def initializeInstance(self, instance, item=None, container=None):
        pass

    security.declarePrivate('initializeField')
    def initializeField(self, instance, field):
        pass

    security.declarePrivate('get')
    def get(self, name, instance, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        value = mdata[self.metadata_set][field.metadata_name]
        return value

    security.declarePrivate('set')
    def set(self, name, instance, value, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        if type(value) == type(u''):
            value = encode(value, instance)
        data = {field.metadata_name:value}
        # Calling _setData directly, because there's
        # *no* method for setting one field at a time,
        # and setValues takes a dict and does
        # validation, which prevents us from setting
        # values.
        mdata._setData(data, set_id=self.metadata_set)

    security.declarePrivate('unset')
    def unset(self, name, instance, **kwargs):
        pass

    security.declarePrivate('cleanupField')
    def cleanupField(self, instance, field, **kwargs):
        pass

    security.declarePrivate('cleanupInstance')
    def cleanupInstance(self, instance, item=None, container=None):
        pass

registerStorage(FacadeMetadataStorage)
