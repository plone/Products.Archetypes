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
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            if idxs == []:
                if hasattr(aq_base(self), 'notifyModified'):
                    self.notifyModified()
            if c is not None:
                c.catalog_object(self, self.__url(), idxs=idxs)
            
    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    def reindexObjectSecurity(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            path = '/'.join(self.getPhysicalPath())
            for brain in c.searchResults(path=path):
                ob = brain.getObject()
                if ob is None:
                    # Ignore old references to deleted objects.
                    continue
                s = getattr(ob, '_p_changed', 0)
                self.reindexObject(idxs=['allowedRolesAndUsers'])
                if s is None: ob._p_deactivate()

            c.catalog_object(self, self.__url(), (['allowedRolesAndUsers']))

