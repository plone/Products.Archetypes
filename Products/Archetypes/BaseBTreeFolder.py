from Products.Archetypes.public import *
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent, \
     AccessContentsInformation, View
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
try:
    from Products.BTreeFolder2.CMFBTreeFolder import CMFBTreeFolder
    has_btree = 1
except ImportError:
    has_btree = 0

if has_btree:
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
            CMFBTreeFolder.manage_afterAdd(self, item, container)

        security.declarePrivate('manage_afterClone')
        def manage_afterClone(self, item):
            BaseFolder.manage_afterClone(self, item)
            CMFBTreeFolder.manage_afterClone(self, item)

        security.declarePrivate('manage_beforeDelete')
        def manage_beforeDelete(self, item, container):
            CMFBTreeFolder.manage_beforeDelete(self, item, container)
            BaseFolder.manage_beforeDelete(self, item, container)

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

        __call__ = SkinnedFolder.__call__

        security.declareProtected(View, 'view')
        view = SkinnedFolder.view

        security.declareProtected(View, 'index_html')
        index_html = SkinnedFolder.index_html

if not has_btree:
    BaseBTreeFolder = BaseFolder

