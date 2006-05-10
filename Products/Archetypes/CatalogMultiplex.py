
from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import CATALOGMAP_USES_PORTALTYPE

class CatalogMultiplex(CMFCatalogAware):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join( self.getPhysicalPath() )

    def getCatalogs(self):
        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return []

        if CATALOGMAP_USES_PORTALTYPE:
            return at.getCatalogsByType(self.portal_type)
        else:
            return at.getCatalogsByType(self.meta_type)

    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        catalogs = self.getCatalogs()
        url = self.__url()
        for c in catalogs:
            c.catalog_object(self, url)
            
    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        catalogs = self.getCatalogs()
        url = self.__url()
        for c in catalogs:
            c.uncatalog_object(url)

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        """update indexes of this object in all registered catalogs.
        
        Catalogs are registered per 'meta_type' in archetypes tool.
        
        'idxs' are a list of index names. If this list is given only the given 
        indexes are refreshed. If a index does not exist in catalog its 
        silently ignored.
        """
        if idxs == [] and hasattr(aq_base(self), 'notifyModified'):
            # Archetypes default setup has this defined in ExtensibleMetadata 
            # mixin. note: this refreshes the 'etag ' too.
            self.notifyModified()

        self.http__refreshEtag()

        catalogs = self.getCatalogs()
        if not catalogs:
            return

        url = self.__url()

        for c in catalogs:
            if c is not None:
                # We want the intersection of the catalogs idxs
                # and the incoming list.
                lst = idxs
                indexes = c.indexes()
                if idxs:
                    lst = [i for i in idxs if i in indexes]
                c.catalog_object(self, url, idxs=lst)

        # We only make this call if idxs is not passed.
        #
        # manage_afterAdd/manage_beforeDelete from Referenceable take
        # care of most of the issues, but some places still expect to
        # call reindexObject and have the uid_catalog updated.
        # TODO: fix this so we can remove the following lines.
        if not idxs:
            if isinstance(self, Referenceable):
                self._catalogUID(self)
                # _catalogRefs used to be called here, but all possible
                # occurrences should be handled by
                # manage_afterAdd/manage_beforeDelete from Referenceable now.

InitializeClass(CatalogMultiplex)
