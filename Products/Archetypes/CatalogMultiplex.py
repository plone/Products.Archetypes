from Products.Archetypes.config import *

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Globals import InitializeClass

class CatalogMultiplex(CMFCatalogAware):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join( self.getPhysicalPath() )

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        at = getToolByName(self, TOOL_NAME, None)
        if not at: return
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.catalog_object(self, self.__url())

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        for c in catalogs:
            c.uncatalog_object(self.__url())

        # Specially control reindexing to UID catalog
        # the pathing makes this needed
        self._uncatalogUID(self)


    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        if idxs == []:
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()

        at = getToolByName(self, TOOL_NAME, None)
        if at is None: return

        catalogs = at.getCatalogsByType(self.meta_type)

        for c in catalogs:
            if c is not None:
                #We want the intersection of the catalogs idxs
                #and the incoming list
                lst = idxs
                indexes = c.indexes()
                if idxs:
                    lst = [i for i in idxs if i in indexes]
                c.catalog_object(self, self.__url(), idxs=lst)

        # Specially control reindexing to UID catalog
        # the pathing makes this needed
        self._catalogUID(self)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        CMFCatalogAware.manage_afterAdd(self, item, container)
        self.indexObject()

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        CMFCatalogAware.manage_afterClone(self, item)
        self.reindexObject()

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        self.unindexObject()

InitializeClass(CatalogMultiplex)
