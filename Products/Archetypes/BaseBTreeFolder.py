from Products.Archetypes.public import BaseFolder
from Products.CMFCore import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder import SkinnedFolder
from Products.BTreeFolder2.CMFBTreeFolder import CMFBTreeFolder

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

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
    def manage_afterAdd(self, item, container):
        # CMFBTreeFolder inherits from PortalFolder, which os the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        # CMFBTreeFolder inherits from PortalFolder, which os the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        # CMFBTreeFolder inherits from PortalFolder, which os the same
        # base class as SkinnedFolder, and SkinnedFolder doesn't
        # override any of those methods, so just calling
        # BaseFolder.manage* should do it.
        BaseFolder.manage_beforeDelete(self, item, container)

    def __getitem__(self, key):
        """ Override BTreeFolder __getitem__ """
        if key in self.Schema().keys() and key[:1] != "_": #XXX 2.2
            accessor = self.Schema()[key].getAccessor(self)
            if accessor is not None:
                return accessor()
        return CMFBTreeFolder.__getitem__(self, key)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'indexObject')
    indexObject = BaseFolder.indexObject

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'unindexObject')
    unindexObject = BaseFolder.unindexObject

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'reindexObject')
    reindexObject = BaseFolder.reindexObject

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'reindexObjectSecurity')
    reindexObjectSecurity = BaseFolder.reindexObjectSecurity

    security.declarePrivate('notifyWorkflowCreated')
    notifyWorkflowCreated = BaseFolder.notifyWorkflowCreated

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueItems')
    opaqueItems = BaseFolder.opaqueItems

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueIds')
    opaqueIds = BaseFolder.opaqueIds

    security.declareProtected(CMFCorePermissions.AccessContentsInformation, 'opaqueValues')
    opaqueValues = BaseFolder.opaqueValues

    security.declareProtected(CMFCorePermissions.ListFolderContents, 'listFolderContents')
    listFolderContents = BaseFolder.listFolderContents

    security.declareProtected(CMFCorePermissions.AccessContentsInformation,
                              'folderlistingFolderContents')
    folderlistingFolderContents = BaseFolder.folderlistingFolderContents

    __call__ = SkinnedFolder.__call__

    security.declareProtected(CMFCorePermissions.View, 'view')
    view = SkinnedFolder.view

    security.declareProtected(CMFCorePermissions.View, 'index_html')
    index_html = SkinnedFolder.index_html

    security.declareProtected(CMFCorePermissions.View, 'Title')
    Title = BaseFolder.Title

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setTitle')
    setTitle = BaseFolder.setTitle

    security.declareProtected(CMFCorePermissions.View, 'title_or_id')
    title_or_id = BaseFolder.title_or_id

    security.declareProtected(CMFCorePermissions.View, 'Description')
    Description = BaseFolder.Description

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setDescription')
    setDescription = BaseFolder.setDescription

InitializeClass(BaseBTreeFolder)


BaseBTreeFolderSchema = BaseBTreeFolder.schema

__all__ = ('BaseBTreeFolder', 'BaseBTreeFolderSchema', )
