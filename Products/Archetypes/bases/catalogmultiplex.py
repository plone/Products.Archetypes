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

from Products.Archetypes.config import *

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Globals import InitializeClass

class CatalogMultiplex(CMFCatalogAware):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join( self.getPhysicalPath() )

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        at = getToolByName(self, TOOL_NAME, None)
        if not at: return
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.catalog_object(self, self.__url())

        self._catalogUID(self)
        self._catalogRefs(self)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.uncatalog_object(self.__url())

        # Specially control reindexing to UID catalog
        # the pathing makes this needed
        self._uncatalogUID(self)
        self._uncatalogRefs(self)

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        if idxs == []:
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()

        at = getToolByName(self, TOOL_NAME, None)
        if at is None: return

        catalogs = at.getCatalogsByType(self.meta_type)

        for c in catalogs:
            if c is not None:
                #We want the intersection of the catalogs idxs
                #and the incoming list
                lst = idxs
                indexes = c.indexes()
                if idxs:
                    lst = [i for i in idxs if i in indexes]
                c.catalog_object(self, self.__url(), idxs=lst)

        self._catalogUID(self)
        self._catalogRefs(self)


    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        self.indexObject()

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        self.reindexObject()

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        self.unindexObject()

InitializeClass(CatalogMultiplex)
