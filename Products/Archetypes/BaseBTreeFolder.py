from Products.Archetypes.public import *

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent, \
     AccessContentsInformation, View, ListFolderContents
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
from Products.BTreeFolder2.CMFBTreeFolder import CMFBTreeFolder

# to keep backward compatibility
has_btree = 1

class BaseBTreeFolder(CMFBTreeFolder, BaseFolder):
    """ A BaseBTreeFolder with all the bells and whistles"""

    security = ClassSecurityInfo()

    __implements__ = (CMFBTreeFolder.__implements__, ) + \
                     (BaseFolder.__implements__, )

    def __init__(self, oid, **kwargs):
        CMFBTreeFolder.__init__(self, id)
        BaseFolder.__init__(self, oid, **kwargs)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        BaseFolder.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        BaseFolder.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        BaseFolder.manage_beforeDelete(self, item, container)

    def __getitem__(self, key):
        """ Override BTreeFolder __getitem__ """
        if key in self.Schema().keys() and key[:1] != "_": #XXX 2.2
            accessor = self.Schema()[key].getAccessor(self)
            if accessor is not None:
                return accessor()
        return CMFBTreeFolder.__getitem__(self, key)

    security.declareProtected(ModifyPortalContent, 'indexObject')
    indexObject = BaseFolder.indexObject

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    unindexObject = BaseFolder.unindexObject

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    reindexObject = BaseFolder.reindexObject

    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    reindexObjectSecurity = BaseFolder.reindexObjectSecurity

    security.declarePrivate('notifyWorkflowCreated')
    notifyWorkflowCreated = BaseFolder.notifyWorkflowCreated

    security.declareProtected(AccessContentsInformation, 'opaqueItems')
    opaqueItems = BaseFolder.opaqueItems

    security.declareProtected(AccessContentsInformation, 'opaqueIds')
    opaqueIds = BaseFolder.opaqueIds

    security.declareProtected(AccessContentsInformation, 'opaqueValues')
    opaqueValues = BaseFolder.opaqueValues

    security.declareProtected(ListFolderContents, 'listFolderContents')
    listFolderContents = BaseFolder.listFolderContents

    security.declareProtected(AccessContentsInformation,
                              'folderlistingFolderContents')
    folderlistingFolderContents = BaseFolder.folderlistingFolderContents

    __call__ = SkinnedFolder.__call__

    security.declareProtected(View, 'view')
    view = SkinnedFolder.view

    security.declareProtected(View, 'index_html')
    index_html = SkinnedFolder.index_html

    security.declareProtected(View, 'Title')
    Title = BaseFolder.Title

    security.declareProtected(ModifyPortalContent, 'setTitle')
    setTitle = BaseFolder.setTitle

    security.declareProtected(View, 'title_or_id')
    title_or_id = BaseFolder.title_or_id

    security.declareProtected(View, 'Description')
    Description = BaseFolder.Description

    security.declareProtected(ModifyPortalContent, 'setDescription')
    setDescription = BaseFolder.setDescription

InitializeClass(BaseBTreeFolder)
