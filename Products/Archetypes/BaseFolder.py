from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder

from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from BaseObject import BaseObject
from I18NMixin import I18NMixin
from debug import log, log_exc
from interfaces.base import IBaseFolder
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata

class BaseFolder(BaseObject, Referenceable, SkinnedFolder, ExtensibleMetadata):
    """ A not-so-basic Folder implementation """

    __implements__ = (IBaseFolder, IReferenceable, IExtensibleMetadata)

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"

    schema = BaseObject.schema + ExtensibleMetadata.schema

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        SkinnedFolder.__init__(self, oid, self.Title())
        BaseObject.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)
        SkinnedFolder.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)
        SkinnedFolder.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)
        SkinnedFolder.manage_beforeDelete(self, item, container)

InitializeClass(BaseFolder)

class I18NBaseFolder(I18NMixin, BaseFolder):
    """ override BaseFolder to have I18N title and description,
    plus I18N related actions
    """
    
    schema = BaseFolder.schema + I18NMixin.schema

    def __init__(self, *args, **kwargs):
        BaseFolder.__init__(self, *args, **kwargs)
        I18NMixin.__init__(self)

InitializeClass(I18NBaseFolder)

