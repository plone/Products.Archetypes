from Products.Archetypes import config
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.debug import log, log_exc

from Acquisition import aq_base, aq_chain
from AccessControl import getSecurityManager,Unauthorized
from ExtensionClass import Base
from OFS.ObjectManager import BeforeDeleteException

from Products.CMFCore.utils import getToolByName
from Products.CMFCore import CMFCorePermissions
from ZODB.PersistentMapping import PersistentMapping
from utils import getRelPath, getRelURL
####
## In the case of a copy we want to lose refs
##                a cut/paste we want to keep refs
##                a delete to lose refs
####


class Referenceable(Base):
    """ A Mix-in for Referenceable objects """
    isReferenceable = 1

    def reference_url(self):
        """like absoluteURL, but return a link to the object with this UID"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.reference_url(self)

    def hasRelationshipTo(self, target, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.hasRelationshipTo(self, target, relationship)

    def addReference(self, object, relationship=None, **kwargs):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.addReference(self, object, relationship, **kwargs)

    def deleteReference(self, target, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.deleteReference(self, target, relationship)

    def deleteReferences(self, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.deleteReferences(self, relationship)

    def getRelationships(self):
        """What kinds of relationships does this object have"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.getRelationships(self)

    def getBRelationships(self):
        """
        What kinds of relationships does this object have from others
        """
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.getBackRelationships(self)

    def getRefs(self, relationship=None):
        """get all the referenced objects for this object"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getReferences(self, relationship)
        if refs:
            return [ref.getTargetObject() for ref in refs]
        return []

    def getBRefs(self, relationship=None):
        """get all the back referenced objects for this object"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getBackReferences(self, relationship)
        if refs:
            return [ref.getSourceObject() for ref in refs]
        return []


    def _register(self, reference_manager=None):
        """register with the archetype tool for a unique id"""
        if self.UID() is not None:
            return

        if reference_manager is None:
            reference_manager = getToolByName(self, config.REFERENCE_CATALOG)
        reference_manager.registerObject(self)

    def _unregister(self):
        """unregister with the archetype tool, remove all references"""
        reference_manager = getToolByName(self, config.REFERENCE_CATALOG)
        reference_manager.unregisterObject(self)

    def _getReferenceAnnotations(self):
        """given an object extract the bag of references for which it
        is the source"""
        if not hasattr(self, config.REFERENCE_ANNOTATION):
            setattr(self, config.REFERENCE_ANNOTATION, PersistentMapping())
        return getattr(self, config.REFERENCE_ANNOTATION)


    def UID(self):
        return getattr(self, config.UUID_ATTR, None)

    ## Hooks
    def manage_afterAdd(self, item, container):
        """
        Get a UID
        (Called when the object is created or moved.)
        """
        ct = getToolByName(container, config.REFERENCE_CATALOG, None)
        self._register(reference_manager=ct)

        # the UID index needs to be updated for any annotations we
        # carry
        self._catalogUID(container)
        self._catalogRefs(container)



    def manage_afterClone(self, item):
        """
        Get a new UID (effectivly dropping reference)
        (Called when the object is cloned.)
        """
        print "MAC", self.UID()
        uc = getToolByName(container, config.UID_CATALOG)

        setattr(self, config.UUID_ATTR, None)
        self._register()
        # the UID index needs to be updated for any annotations we
        # carry
        self._catalogUID(self)
        self._catalogRefs(self)

    def manage_beforeDelete(self, item, container):
        """
            Remove self from the catalog.
            (Called when the object is deleted or moved.)
        """
        storeRefs = getattr(self, '_v_cp_refs', None)
        if storeRefs is None:
            rc = getToolByName(container, config.REFERENCE_CATALOG)
            references = rc.getReferences(self)
            back_references = rc.getBackReferences(self)
            try:
                #First check the 'delete cascade' case
                if references:
                    for ref in references:
                        ref.beforeSourceDeleteInformTarget()
                #Then check the 'holding/ref count' case
                if back_references:
                    for ref in back_references:
                        ref.beforeTargetDeleteInformSource()
                # If nothing prevented it, remove all the refs
                self.deleteReferences()
            except ReferenceException, E:
                raise BeforeDeleteException(E)


        # Track the UUID
        self._uncatalogUID(container)
        self._uncatalogRefs(container)

        #and reset the flag
        self._v_cp_refs = None

    ## Catalog Helper methods
    def _catalogUID(self, aq):
        uc = getToolByName(aq, config.UID_CATALOG)
        url = getRelURL(aq, self.getPhysicalPath())
        uc.catalog_object(self, url)

    def _uncatalogUID(self, aq):
        uc = getToolByName(aq, config.UID_CATALOG)
        url = getRelURL(aq, self.getPhysicalPath())
        uc.uncatalog_object(url)

    def _catalogRefs(self, aq):
        annotations = self._getReferenceAnnotations()
        if annotations:
            uc = getToolByName(aq, config.UID_CATALOG)
            rc = getToolByName(aq, config.REFERENCE_CATALOG)
            for ref in annotations.values():
                ref = aq_base(ref).__of__(self)
                url = '/'.join(ref.getPhysicalPath())
                uc.catalog_object(ref, url)
                rc.catalog_object(ref, url)

    def _uncatalogRefs(self, aq):
        annotations = self._getReferenceAnnotations()
        if annotations:
            uc = getToolByName(aq, config.UID_CATALOG)
            rc = getToolByName(aq, config.REFERENCE_CATALOG)
            for ref in annotations.values():
                url = ref.getURL()
                uc.uncatalog_object(url)
                rc.uncatalog_object(url)

    # CopyPaste hack
    def _notifyOfCopyTo(self, container, op=0):
        """keep reference info internally when op == 1 (move)
        because in those cases we need to keep refs"""
        ## This isn't really safe for concurrent usage, but the
        ## worse case is not that bad and could be fixed with a reindex
        ## on the archetype tool
        if op==1: self._v_cp_refs =  1
