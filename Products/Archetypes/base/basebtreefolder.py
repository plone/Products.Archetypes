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

from Products.Archetypes.base.basefolder import BaseFolder
from Products.CMFCore import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder import SkinnedFolder
from Products.BTreeFolder2.CMFBTreeFolder import CMFBTreeFolder

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from webdav.NullResource import NullResource
from OFS.ObjectManager import REPLACEABLE
from ComputedAttribute import ComputedAttribute

# to keep backward compatibility
has_btree = 1

class BaseBTreeFolder(CMFBTreeFolder, BaseFolder):
    """ A BaseBTreeFolder with all the bells and whistles"""

    security = ClassSecurityInfo()

    __implements__ = CMFBTreeFolder.__implements__, BaseFolder.__implements__

    def __init__(self, oid, **kwargs):
        CMFBTreeFolder.__init__(self, id)
        BaseFolder.__init__(self, oid, **kwargs)

    security.declarePrivate('manage_afterAdd')
    manage_afterAdd = BaseFolder.manage_afterAdd.im_func

    security.declarePrivate('manage_afterClone')
    manage_afterClone = BaseFolder.manage_afterClone.im_func

    security.declarePrivate('manage_beforeDelete')
    manage_beforeDelete = BaseFolder.manage_beforeDelete.im_func

    def __getitem__(self, key):
        """ Override BTreeFolder __getitem__ """
        if key in self.Schema().keys() and key[:1] != "_": #XXX 2.2
            accessor = self.Schema()[key].getAccessor(self)
            if accessor is not None:
                return accessor()
        return CMFBTreeFolder.__getitem__(self, key)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'indexObject')
    indexObject = BaseFolder.indexObject.im_func

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'unindexObject')
    unindexObject = BaseFolder.unindexObject.im_func

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'reindexObject')
    reindexObject = BaseFolder.reindexObject.im_func

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'reindexObjectSecurity')
    reindexObjectSecurity = BaseFolder.reindexObjectSecurity.im_func

    security.declarePrivate('notifyWorkflowCreated')
    notifyWorkflowCreated = BaseFolder.notifyWorkflowCreated.im_func

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueItems')
    opaqueItems = BaseFolder.opaqueItems

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueIds')
    opaqueIds = BaseFolder.opaqueIds.im_func

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueValues')
    opaqueValues = BaseFolder.opaqueValues.im_func

    security.declareProtected(CMFCorePermissions.ListFolderContents, 'listFolderContents')
    listFolderContents = BaseFolder.listFolderContents.im_func

    security.declareProtected(CMFCorePermissions.AccessContentsInformation,
                              'folderlistingFolderContents')
    folderlistingFolderContents = BaseFolder.folderlistingFolderContents.im_func

    __call__ = SkinnedFolder.__call__.im_func

    security.declareProtected(CMFCorePermissions.View, 'view')
    view = SkinnedFolder.view.im_func

    def index_html(self):
        """ Allow creation of .
        """
        if self.has_key('index_html'):
            return self._getOb('index_html')
        request = getattr(self, 'REQUEST', None)
        if request and request.has_key('REQUEST_METHOD'):
            if (request.maybe_webdav_client and
                request['REQUEST_METHOD'] in  ['PUT']):
                # Very likely a WebDAV client trying to create something
                nr = NullResource(self, 'index_html')
                nr.__replaceable__ = REPLACEABLE
                return nr
        return None

    index_html = ComputedAttribute(index_html, 1)

    security.declareProtected(CMFCorePermissions.View, 'Title')
    Title = BaseFolder.Title.im_func

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setTitle')
    setTitle = BaseFolder.setTitle.im_func

    security.declareProtected(CMFCorePermissions.View, 'title_or_id')
    title_or_id = BaseFolder.title_or_id.im_func

    security.declareProtected(CMFCorePermissions.View, 'Description')
    Description = BaseFolder.Description.im_func

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setDescription')
    setDescription = BaseFolder.setDescription.im_func

    manage_addFolder = BaseFolder.manage_addFolder.im_func

InitializeClass(BaseBTreeFolder)


BaseBTreeFolderSchema = BaseBTreeFolder.schema

__all__ = ('BaseBTreeFolder', 'BaseBTreeFolderSchema', )
