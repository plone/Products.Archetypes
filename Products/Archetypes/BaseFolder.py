from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.CatalogMultiplex  import CatalogMultiplex
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.interfaces.base import IBaseFolder
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.Schema.Provider import SchemaProvider

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.PortalContent  import PortalContent
from Products.CMFDefault.SkinnedFolder  import SkinnedFolder
from OFS.Folder import Folder

class BaseFolderMixin(SchemaProvider,
                      BaseObject,
                      Referenceable,
                      CatalogMultiplex,
                      SkinnedFolder,
                      Folder
                      ):
    """A not-so-basic Folder implementation, with no Dublin Core
    Metadata"""

    __implements__ = (IBaseFolder, IReferenceable) + \
                     PortalContent.__implements__

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        # Call skinned first cause baseobject will set new defaults on
        # those attributes anyway
        SchemaProvider.__init__(self)
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
