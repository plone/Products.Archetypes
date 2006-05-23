from Products.Archetypes import WebDAVSupport
from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.interfaces.base import IBaseContent as z2IBaseContent
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex

from Acquisition import aq_base
from Acquisition import aq_get
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.History import Historical
from Products.CMFCore import permissions
from Products.CMFCore.PortalContent import PortalContent
from OFS.PropertyManager import PropertyManager

from Products.Archetypes.interfaces import IBaseContent
from zope.interface import implements

class BaseContentMixin(CatalogMultiplex,
                       BaseObject,
                       PortalContent,
                       Historical):
    """A not-so-basic CMF Content implementation that doesn't
    include Dublin Core Metadata"""

    __implements__ = z2IBaseContent, IReferenceable, PortalContent.__implements__
    implements(IBaseContent)

    security = ClassSecurityInfo()
    manage_options = PortalContent.manage_options + Historical.manage_options

    isPrincipiaFolderish = 0
    isAnObjectManager = 0
    __dav_marshall__ = True

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
        self._v_cp_refs = None

    security.declareProtected(permissions.ModifyPortalContent, 'PUT')
    PUT = WebDAVSupport.PUT

    security.declareProtected(permissions.View, 'manage_FTPget')
    manage_FTPget = WebDAVSupport.manage_FTPget

    security.declarePrivate('manage_afterPUT')
    manage_afterPUT = WebDAVSupport.manage_afterPUT

InitializeClass(BaseContentMixin)

class BaseContent(BaseContentMixin,
                  ExtensibleMetadata,
                  PropertyManager):
    """A not-so-basic CMF Content implementation with Dublin Core
    Metadata included"""

    __implements__ = BaseContentMixin.__implements__, IExtensibleMetadata

    schema = BaseContentMixin.schema + ExtensibleMetadata.schema

    manage_options = BaseContentMixin.manage_options + \
        PropertyManager.manage_options

    def __init__(self, oid, **kwargs):
        BaseContentMixin.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

InitializeClass(BaseContent)


BaseSchema = BaseContent.schema

__all__ = ('BaseContent', 'BaseContentMixin', 'BaseSchema', )
