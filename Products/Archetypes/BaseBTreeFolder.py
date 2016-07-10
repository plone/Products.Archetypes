from Products.Archetypes import WebDAVSupport
from Products.Archetypes.atapi import BaseFolder
from Products.Archetypes.interfaces import IBaseFolder
from Products.CMFCore import permissions
from Products.CMFCore.CMFBTreeFolder import CMFBTreeFolder
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from zope.interface import implementer

# to keep backward compatibility
has_btree = 1

from webdav.NullResource import NullResource
from OFS.ObjectManager import REPLACEABLE
from ComputedAttribute import ComputedAttribute

from plone.app.folder.base import BaseBTreeFolder as Base


class BaseBTreeFolder(Base):

    _ordering = 'unordered'     # old large folder remain unordered at first


@implementer(IBaseFolder)
class ObsoleteBaseBTreeFolder(CMFBTreeFolder, BaseFolder):
    """ A BaseBTreeFolder with all the bells and whistles"""

    security = ClassSecurityInfo()

    # Fix permissions set by CopySupport.py
    __ac_permissions__ = (
        (permissions.ModifyPortalContent,
         ('manage_cutObjects', 'manage_pasteObjects',
          'manage_renameObject', 'manage_renameObjects',)),
    )
    security.declareProtected('Copy or Move', 'manage_copyObjects')

    def __init__(self, oid, **kwargs):
        CMFBTreeFolder.__init__(self, oid)
        BaseFolder.__init__(self, oid, **kwargs)

    security.declarePrivate('manage_afterAdd')

    def manage_afterAdd(self, item, container):
        # CMFBTreeFolder inherits from PortalFolder, which has the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')

    def manage_afterClone(self, item):
        # CMFBTreeFolder inherits from PortalFolder, which has the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')

    def manage_beforeDelete(self, item, container):
        # CMFBTreeFolder inherits from PortalFolder, which has the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_beforeDelete(self, item, container)

    def _getCopy(self, container):
        # We need to take _getCopy from BaseFolder (implicitly from
        # Referenceable) instead of straight from PortalFolder, otherwise there
        # are strange side effects with references on copy.
        return BaseFolder._getCopy(self, container)

    def _notifyOfCopyTo(self, container, op=0):
        # We need to take _notifyOfCopyTo from BaseFolder (implicitly from
        # Referenceable) instead of straight from PortalFolder, otherwise there
        # are strange side effects with references on copy.
        return BaseFolder._notifyOfCopyTo(self, container, op)

    def __getitem__(self, key):
        """ Override BTreeFolder __getitem__ """
        if key in self.Schema().keys() and key[:1] != "_":  # XXX 2.2
            accessor = self.Schema()[key].getAccessor(self)
            if accessor is not None:
                return accessor()
        return CMFBTreeFolder.__getitem__(self, key)

    security.declareProtected(permissions.ModifyPortalContent, 'indexObject')
    indexObject = BaseFolder.indexObject.im_func

    security.declareProtected(permissions.ModifyPortalContent, 'unindexObject')
    unindexObject = BaseFolder.unindexObject.im_func

    security.declareProtected(permissions.ModifyPortalContent, 'reindexObject')
    reindexObject = BaseFolder.reindexObject.im_func

    security.declareProtected(
        permissions.ModifyPortalContent, 'reindexObjectSecurity')
    reindexObjectSecurity = BaseFolder.reindexObjectSecurity.im_func

    security.declarePrivate('notifyWorkflowCreated')
    notifyWorkflowCreated = BaseFolder.notifyWorkflowCreated.im_func

    security.declareProtected(
        permissions.AccessContentsInformation, 'opaqueItems')
    opaqueItems = BaseFolder.opaqueItems.im_func

    security.declareProtected(
        permissions.AccessContentsInformation, 'opaqueIds')
    opaqueIds = BaseFolder.opaqueIds.im_func

    security.declareProtected(
        permissions.AccessContentsInformation, 'opaqueValues')
    opaqueValues = BaseFolder.opaqueValues.im_func

    security.declareProtected(
        permissions.ListFolderContents, 'listFolderContents')
    listFolderContents = BaseFolder.listFolderContents.im_func

    security.declareProtected(permissions.AccessContentsInformation,
                              'folderlistingFolderContents')
    folderlistingFolderContents = BaseFolder.folderlistingFolderContents.im_func

    __call__ = BaseFolder.__call__.im_func

    #security.declareProtected(permissions.View, 'view')
    #view = BaseFolder.view.im_func

    def index_html(self):
        """ Allow creation of .
        """
        if 'index_html' in self:
            return self._getOb('index_html')
        request = getattr(self, 'REQUEST', None)
        if request and 'REQUEST_METHOD' in request:
            if (request.maybe_webdav_client and
                    request['REQUEST_METHOD'] in ['PUT']):
                # Very likely a WebDAV client trying to create something
                nr = NullResource(self, 'index_html')
                nr.__replaceable__ = REPLACEABLE
                return nr
        return None

    index_html = ComputedAttribute(index_html, 1)

    security.declareProtected(permissions.View, 'Title')
    Title = BaseFolder.Title.im_func

    security.declareProtected(permissions.ModifyPortalContent, 'setTitle')
    setTitle = BaseFolder.setTitle.im_func

    security.declareProtected(permissions.View, 'title_or_id')
    title_or_id = BaseFolder.title_or_id.im_func

    security.declareProtected(permissions.View, 'Description')
    Description = BaseFolder.Description.im_func

    security.declareProtected(
        permissions.ModifyPortalContent, 'setDescription')
    setDescription = BaseFolder.setDescription.im_func

    manage_addFolder = BaseFolder.manage_addFolder.im_func

    MKCOL = BaseFolder.MKCOL.im_func
    MKCOL_handler = BaseFolder.MKCOL_handler.im_func

    security.declareProtected(permissions.ModifyPortalContent, 'PUT')
    PUT = WebDAVSupport.PUT

    security.declareProtected(permissions.View, 'manage_FTPget')
    manage_FTPget = WebDAVSupport.manage_FTPget

    security.declarePrivate('manage_afterPUT')
    manage_afterPUT = WebDAVSupport.manage_afterPUT

    security.declareProtected(permissions.ModifyPortalContent, 'edit')
    edit = BaseFolder.edit.im_func

InitializeClass(BaseBTreeFolder)

BaseBTreeFolderSchema = BaseBTreeFolder.schema

__all__ = ('BaseBTreeFolder', 'BaseBTreeFolderSchema', )
