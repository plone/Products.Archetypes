from logging import WARNING

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CatalogAware, WorkflowAware, OpaqueItemManager
from Products.Archetypes.config import CATALOGMAP_USES_PORTALTYPE, TOOL_NAME
from Products.Archetypes.log import log
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.utils import shasattr, isFactoryContained

class CatalogMultiplex(CatalogAware, WorkflowAware, OpaqueItemManager):
    security = ClassSecurityInfo()

    def __url(self):
        return '/'.join(self.getPhysicalPath())

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
        if isFactoryContained(self):
            return
        catalogs = self.getCatalogs()
        url = self.__url()
        for c in catalogs:
            c.catalog_object(self, url)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        if isFactoryContained(self):
            return
        catalogs = self.getCatalogs()
        url = self.__url()
        for c in catalogs:
            if c._catalog.uids.get(url, None) is not None:
                c.uncatalog_object(url)

    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    def reindexObjectSecurity(self, skip_self=False):
        """update security information in all registered catalogs.
        """
        if isFactoryContained(self):
            return
        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return

        catalogs = [c for c in at.getCatalogsByType(self.meta_type)
                               if ICatalogTool.providedBy(c)]
        path = self.__url()

        for catalog in catalogs:
            for brain in catalog.unrestrictedSearchResults(path=path):
                brain_path = brain.getPath()
                if brain_path == path and skip_self:
                    continue

                # Get the object
                if hasattr(aq_base(brain), '_unrestrictedGetObject'):
                    ob = brain._unrestrictedGetObject()
                else:
                    # BBB: Zope 2.7
                    ob = self.unrestrictedTraverse(brain_path, None)
                if ob is None:
                    # BBB: Ignore old references to deleted objects.
                    # Can happen only in Zope 2.7, or when using
                    # catalog-getObject-raises off in Zope 2.8
                    log("reindexObjectSecurity: Cannot get %s from catalog" %
                        brain_path, level=WARNING)
                    continue

                # Recatalog with the same catalog uid.
                catalog.reindexObject(ob, idxs=self._cmf_security_indexes,
                                        update_metadata=0, uid=brain_path)



    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        """update indexes of this object in all registered catalogs.

        Catalogs are registered per 'meta_type' in archetypes tool.

        'idxs' are a list of index names. If this list is given only the given
        indexes are refreshed. If a index does not exist in catalog its
        silently ignored.
        """
        if isFactoryContained(self):
            return
        if idxs == [] and shasattr(self, 'notifyModified'):
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
                isCopy = getattr(self, '_v_is_cp', None)
                if isCopy is None:
                    self._catalogUID(self)

InitializeClass(CatalogMultiplex)
