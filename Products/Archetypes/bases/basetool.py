from Products.Archetypes.bases.basecontent import BaseContentMixin
from Products.Archetypes.bases.basefolder import BaseFolderMixin

from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.utils import UniqueObject

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.PropertyManager import PropertyManager
from ZODB.POSException import ConflictError

class BaseTool(UniqueObject, BaseContentMixin, PropertyManager,
    ActionProviderBase):
    """TODO
    """
    
    security = ClassSecurityInfo()

InitializeClass(BaseTool)

class BaseFolderishTool(UniqueObject, BaseFolderMixin, PropertyManager,
    ActionProviderBase):
    """TODO
    """
    
    security = ClassSecurityInfo()

InitializeClass(BaseFolderishTool)

__all__ = ('BaseTool', 'BaseFolderishTool', )
