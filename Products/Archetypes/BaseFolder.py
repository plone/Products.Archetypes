from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from BaseObject import BaseObject
from debug import log, log_exc
from interfaces.base import IBaseFolder
from interfaces.referenceable import IReferenceable

class BaseFolder(BaseObject, Referenceable, SkinnedFolder, ExtensibleMetadata):
    """ A not-so-basic Folder implementation """
    
    __implements__ = (IBaseFolder, IReferenceable)

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        SkinnedFolder.__init__(self, oid, self.Title())
        ExtensibleMetadata.__init__(self, **kwargs)
        BaseObject.__init__(self, oid, **kwargs)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)

InitializeClass(BaseFolder)

