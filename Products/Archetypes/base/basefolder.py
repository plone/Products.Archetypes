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

from Products.Archetypes.refengine.referenceable import Referenceable
from Products.Archetypes.base.catalogmultiplex  import CatalogMultiplex
from Products.Archetypes.base.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.base.baseobject import BaseObject
from Products.Archetypes.interfaces.base import IBaseFolder
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.PortalContent  import PortalContent
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
from Products.CMFCore.utils import getToolByName

class BaseFolderMixin(CatalogMultiplex,
                    BaseObject,
                    SkinnedFolder,
                    # XXX Referenceable # this was disabled in 1.3 - why?
                    ):
    """A not-so-basic Folder implementation, with no Dublin Core
    Metadata"""

    __implements__ = IBaseFolder, IReferenceable, PortalContent.__implements__

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"
    use_folder_tabs = 1

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        # Call skinned first cause baseobject will set new defaults on
        # those attributes anyway
        SkinnedFolder.__init__(self, oid, self.Title())
        BaseObject.__init__(self, oid, **kwargs)

    def _notifyOfCopyTo(self, container, op=0):
        """In the case of a move (op=1) we need to make sure
        references are mainained for all referencable objects within
        the one being moved.

        manage_renameObject calls _notifyOfCopyTo so that the
        object being renamed doesn't lose its references. But
        manage_renameObject calls _delObject which calls
        manage_beforeDelete on all the children of the object
        being renamed which deletes all references for children
        of the object being renamed. Here is a patch that does
        recursive calls for _notifyOfCopyTo to address that
        problem.
        """
        BaseObject._notifyOfCopyTo(self, container, op=op)
        SkinnedFolder._notifyOfCopyTo(self, container, op=op)
        if op==1: # For efficiency, remove if op==0 needs something
            for child in self.contentValues():
                if IReferenceable.isImplementedBy(child):
                    child._notifyOfCopyTo(self, op)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        BaseObject.manage_afterAdd(self, item, container)
        SkinnedFolder.manage_afterAdd(self, item, container)
        CatalogMultiplex.manage_afterAdd(self, item, container)


    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        BaseObject.manage_afterClone(self, item)
        CatalogMultiplex.manage_afterClone(self, item)
        SkinnedFolder.manage_afterClone(self, item)


    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        BaseObject.manage_beforeDelete(self, item, container)
        CatalogMultiplex.manage_beforeDelete(self, item, container)
        SkinnedFolder.manage_beforeDelete(self, item, container)

        #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
        self._v_cp_refs = None


    security.declareProtected(CMFCorePermissions.DeleteObjects,
                              'manage_delObjects')
    def manage_delObjects(self, ids=[], REQUEST=None):
        """ We need to enforce security. """
        mt=getToolByName(self, 'portal_membership')
        if isinstance(ids, str):
            ids = [ids]
        for id in ids:
            item = self._getOb(id)
            if not mt.checkPermission(CMFCorePermissions.DeleteObjects, item):
                raise Unauthorized, (
                    "Do not have permissions to remove this object")
        SkinnedFolder.manage_delObjects(self, ids, REQUEST=REQUEST)

    security.declareProtected(CMFCorePermissions.ListFolderContents,
                              'listFolderContents')
    def listFolderContents(self, spec=None, contentFilter=None,
                           suppressHiddenFiles=0):
        """
        Optionally you can suppress "hidden" files, or files that begin with .
        """
        contents=SkinnedFolder.listFolderContents(self,
                                                  spec=spec,
                                                  contentFilter=contentFilter)
        if suppressHiddenFiles:
            contents=[obj for obj in contents if obj.getId()[:1]!='.']

        return contents

    security.declareProtected(CMFCorePermissions.AccessContentsInformation,
                              'folderlistingFolderContents')
    def folderlistingFolderContents(self, spec=None, contentFilter=None,
                                    suppressHiddenFiles=0 ):
        """
        Calls listFolderContents in protected only by ACI so that folder_listing
        can work without the List folder contents permission, as in CMFDefault
        """
        return self.listFolderContents(spec, contentFilter, suppressHiddenFiles)

    security.declareProtected(CMFCorePermissions.View, 'Title')
    def Title(self, **kwargs):
        """We have to override Title here to handle arbitrary
        arguments since PortalFolder defines it."""
        return self.getField('title').get(self, **kwargs)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setTitle')
    def setTitle(self, value, **kwargs):
        """We have to override setTitle here to handle arbitrary
        arguments since PortalFolder defines it."""
        self.getField('title').set(self, value, **kwargs)

    def __getitem__(self, key):
        """Overwrite __getitem__

        At first it's using the BaseObject version. If the element can't be
        retrieved from the schema it's using SkinnedFolder as fallback which
        should be the ObjectManager's version.
        """
        try:
            return BaseObject.__getitem__(self, key)
        except KeyError:
            return SkinnedFolder.__getitem__(self, key)

    # override "CMFCore.PortalFolder.PortalFolder.manage_addFolder"
    # as it insists on creating folders of type "Folder".
    # use instead "_at_type_subfolder" or our own type.
    def manage_addFolder( self
                        , id
                        , title=''
                        , REQUEST=None
                        , type_name = None
                        ):
        """ Add a new folder-like object with id *id*.

        IF present, use the parent object's 'mkdir' alias; otherwise, just add
        a PortalFolder.
        """
        ti = self.getTypeInfo()
        # XXX getMethodURL is part of CMF 1.5 but AT 1.3 should be compatible
        # with CMF 1.4
        try:
            method = ti and ti.getMethodURL('mkdir') or None
        except AttributeError:
            method = None
        if method is not None:
            # call it
            getattr(self, method)(id=id)
        else:
            if type_name is None:
                type_name = getattr(self, '_at_type_subfolder', None)
            if type_name is None:
                type_name = ti and ti.getId() or 'Folder'
            self.invokeFactory( type_name, id=id )

        ob = self._getOb( id )
        try:
            ob.setTitle( title )
        except AttributeError:
            pass
        try:
            ob.reindexObject()
        except AttributeError:
            pass

InitializeClass(BaseFolderMixin)


class BaseFolder(BaseFolderMixin, ExtensibleMetadata):
    """A not-so-basic Folder implementation, with Dublin Core
    Metadata included"""

    __implements__ = BaseFolderMixin.__implements__, IExtensibleMetadata

    schema = BaseFolderMixin.schema + ExtensibleMetadata.schema

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        # Call skinned first cause baseobject will set new defaults on
        # those attributes anyway
        BaseFolderMixin.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declareProtected(CMFCorePermissions.View,
                              'Description')
    def Description(self, **kwargs):
        """We have to override Description here to handle arbitrary
        arguments since PortalFolder defines it."""
        return self.getField('description').get(self, **kwargs)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setDescription')
    def setDescription(self, value, **kwargs):
        """We have to override setDescription here to handle arbitrary
        arguments since PortalFolder defines it."""
        self.getField('description').set(self, value, **kwargs)

InitializeClass(BaseFolder)


BaseFolderSchema = BaseFolder.schema

__all__ = ('BaseFolder', 'BaseFolderMixin', 'BaseFolderSchema', )
