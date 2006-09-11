from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import shasattr


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

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        at = getToolByName(self, TOOL_NAME)
        catalogs = at.getCatalogsByType(self.meta_type)
        url = self.__url()
        for c in catalogs:
            c.uncatalog_object(url)

    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    def reindexObjectSecurity(self, skip_self=False):
        """update security information in all registered catalogs.
        """
        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return

        catalogs = [c for c in at.getCatalogsByType(self.meta_type)
                                if c is not None]
        path = '/'.join(self.getPhysicalPath())

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
                    LOG('reindexObjectSecurity', PROBLEM,
                            "Cannot get %s from catalog" % brain_path)
                    continue

                # Recatalog with the same catalog uid.
                try:
                    indexes=self._cmf_security_indexes
                    catalog.reindexObject(ob, idxs=indexes, update_metadata=0,
                                            uid=brain_path)
                except AttributeError:
                    # BBB: CMF 1.4
                    indexes=['allowedRolesAndUsers']
                    catalog.reindexObject(ob, idxs=indexes)



    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        """update indexes of this object in all registered catalogs.

        Catalogs are registered per 'meta_type' in archetypes tool.

        'idxs' are a list of index names. If this list is given only the given
        indexes are refreshed. If a index does not exist in catalog its
        silently ignored.
        """
        if idxs == [] and shasattr(self, 'notifyModified'):
            # Archetypes default setup has this defined in ExtensibleMetadata
            # mixin. note: this refreshes the 'etag ' too.
            self.notifyModified()

        self.http__refreshEtag()

        at = getToolByName(self, TOOL_NAME, None)
        if at is None:
            return

        catalogs = at.getCatalogsByType(self.meta_type)
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
