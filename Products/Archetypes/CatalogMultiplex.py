from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import shasattr
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
            # XXX This is an ugly workaround. This method shouldn't be called
            # twice for an object in the first place, so we don't have to check
            # if it is not cataloged so far. 
            rid = c.getrid(url)
            if rid is None:
                c.catalog_object(self, url)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        catalogs = self.getCatalogs()
        url = self.__url()
        for c in catalogs:
            # XXX This is an ugly workaround. This method shouldn't be called
            # twice for an object in the first place, so we don't have to check
            # if it is still cataloged. 
            rid = c.getrid(url)
            if rid is not None:
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
                self._catalogUID(self)

    # Hooks copied from CMFCore.CMFCatalogAware of CMF 1.6 
    # ----------------------------------------------------

    def manage_afterAdd(self, item, container):
        """
            Add self to the catalog.
            (Called when the object is created or moved.)
        """
        self.indexObject()

    def manage_afterClone(self, item):
        """
            Add self to the workflow.
            (Called when the object is cloned.)
        """
        self.notifyWorkflowCreated()

    def manage_beforeDelete(self, item, container):
        """
            Remove self from the catalog.
            (Called when the object is deleted or moved.)
        """
        self.unindexObject()
        #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
        self._v_cp_refs = None

InitializeClass(CatalogMultiplex)
