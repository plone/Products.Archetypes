from Products.Archetypes.config import *

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Referenceable import Referenceable
from Globals import InitializeClass

class CatalogMultiplex(CMFCatalogAware):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join( self.getPhysicalPath() )

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return
        catalogs = at.getCatalogsByType(self.meta_type)
        url = self.__url()
        for c in catalogs:
            c.catalog_object(self, url)

        self._catalogUID(self)
        self._catalogRefs(self)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        url = self.__url()
        for c in catalogs:
            c.uncatalog_object(url)

        # Specially control reindexing to UID catalog
        # the pathing makes this needed
        self._uncatalogUID(self)
        self._uncatalogRefs(self)

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        if idxs == []:
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()

        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return

        catalogs = at.getCatalogsByType(self.meta_type)
        url = self.__url()

        for c in catalogs:
            if c is not None:
                #We want the intersection of the catalogs idxs
                #and the incoming list
                lst = idxs
                indexes = c.indexes()
                if idxs:
                    lst = [i for i in idxs if i in indexes]
                c.catalog_object(self, url, idxs=lst)
        self._catalogUID(self)
        self._catalogRefs(self)
        self.http__refreshEtag()

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        # For some reason CMFCatalogAware doesn't fully reindex on copy,
        # though it does do a workflow update which reindexes state and
        # security, as a result we have to be a little redundant here.  The
        # super-class method also recurses through sub-objects which is
        # essential.
        self.reindexObject()
        CMFCatalogAware.manage_afterClone(self, item)

InitializeClass(CatalogMultiplex)
