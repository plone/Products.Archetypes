from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName

from config import *

class CatalogMultiplex(CMFCatalogAware):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join( self.getPhysicalPath() )

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.catalog_object(self, self.__url())

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.uncatalog_object(self.__url())

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        if idxs == []:
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()

        at = getToolByName(self, TOOL_NAME, None)
        if at is not None:
            catalogs = at.getCatalogsByType(self.meta_type)

            for c in catalogs:
                if c is not None:
                    c.catalog_object(self, self.__url(), idxs=idxs)
