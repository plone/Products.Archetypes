from Products.Archetypes.config import *

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
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

        # XXX This used to be called from here, but manage_afterAdd
        # should take care of it.
        # self._catalogUID(self)
        # self._catalogRefs(self)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        url = self.__url()
        for c in catalogs:
            c.uncatalog_object(url)

        # XXX This used to be called from here, but manage_beforeDelete
        # should take care of it.
        # self._uncatalogUID(self)
        # self._uncatalogRefs(self)

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

        # We only make this call if idxs is not passed.
        #
        # manage_afterAdd/manage_beforeDelete from Referenceable take
        # care of most of the issues, but some places still expect to
        # call reindexObject and have the uid_catalog updated.
        if not idxs:
            if isinstance(self, Referenceable):
                self._catalogUID(self)
                # _catalogRefs used to be called here, but all possible
                # occurrences should be handled by
                # manage_afterAdd/manage_beforeDelete from Referenceable
                # now.
                # self._catalogRefs(self)
        self.http__refreshEtag()

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        # XXX Seems like we don't need this anymore because
        # indexObject is called on manage_afterAdd.
        # self.reindexObject()

        CMFCatalogAware.manage_afterClone(self, item)

InitializeClass(CatalogMultiplex)
