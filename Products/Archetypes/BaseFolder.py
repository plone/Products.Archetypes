from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
from OFS.Folder import Folder
from Referenceable import Referenceable
from CatalogMultiplex  import CatalogMultiplex
from ExtensibleMetadata import ExtensibleMetadata
from BaseObject import BaseObject
from debug import log, log_exc
from interfaces.base import IBaseFolder
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata

class BaseFolderMixin(BaseObject,
                      Referenceable,
                      CatalogMultiplex,
                      SkinnedFolder,
                      Folder
                      ):
    """A not-so-basic Folder implementation, with no Dublin Core
    Metadata"""

    __implements__ = (IBaseFolder, IReferenceable,
                      SkinnedFolder.__implements__,
                      Folder.__implements__,)

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        # Call skinned first cause baseobject will set new defaults on
        # those attributes anyway
        SkinnedFolder.__init__(self, oid, self.Title())
        BaseObject.__init__(self, oid, **kwargs)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)
        Folder.manage_afterAdd(self, item, container)
        CatalogMultiplex.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)
        Folder.manage_afterClone(self, item)
        CatalogMultiplex.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)
        Folder.manage_beforeDelete(self, item, container)
        CatalogMultiplex.manage_beforeDelete(self, item, container)

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

InitializeClass(BaseFolderMixin)


class BaseFolder(BaseFolderMixin, ExtensibleMetadata):
    """A not-so-basic Folder implementation, with Dublin Core
    Metadata included"""

    __implements__ = (BaseFolderMixin.__implements__ +
                      (IExtensibleMetadata,))

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
