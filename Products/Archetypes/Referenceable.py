from Products.Archetypes import config
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.interfaces.referenceable import IReferenceable


from Acquisition import aq_base, aq_chain, aq_parent
from AccessControl import getSecurityManager,Unauthorized
from ExtensionClass import Base
from OFS.ObjectManager import BeforeDeleteException

from Products.CMFCore.utils import getToolByName
from Products.CMFCore import CMFCorePermissions
from OFS.Folder import Folder
from utils import getRelPath, getRelURL
####
## In the case of a copy we want to lose refs
##                a cut/paste we want to keep refs
##                a delete to lose refs
####


class Referenceable(Base):
    """ A Mix-in for Referenceable objects """
    isReferenceable = 1

    __implements__ = (IReferenceable,)
    
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

    #aliases
    getReferences=getRefs
    getBackReferences=getBRefs
    
    def getReferenceImpl(self, relationship=None):
        """get all the reference objects for this object    """
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getReferences(self, relationship)
        if refs:
            return refs
        return []

    def getBackReferenceImpl(self, relationship=None):
        """get all the back reference objects for this object"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getBackReferences(self, relationship)
        if refs:
            return refs
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
        if not hasattr(aq_base(self), config.REFERENCE_ANNOTATION):
            setattr(self, config.REFERENCE_ANNOTATION, Folder(config.REFERENCE_ANNOTATION))

        return getattr(self, config.REFERENCE_ANNOTATION).__of__(self)


    def UID(self):
        return getattr(self, config.UUID_ATTR, None)

    def _updateCatalog(self, container):
        """Update catalog after copy, rename ...
        """
        # the UID index needs to be updated for any annotations we
        # carry
        
        try:
            uc = getToolByName(container, config.UID_CATALOG)
        except AttributeError:
            # XXX when trying to rename or copy a whole site than container is
            # the object "under" the portal so we can NEVER ever find the catalog
            # which is bad ...
            container = aq_parent(self)
            uc = getToolByName(container, config.UID_CATALOG)

        rc = getToolByName(container, config.REFERENCE_CATALOG)
        
        self._catalogUID(container, uc=uc)
        self._catalogRefs(container, uc=uc, rc=rc)
            

    ## Hooks
    def manage_afterAdd(self, item, container):
        """
        Get a UID
        (Called when the object is created or moved.)
        """
        ct = getToolByName(container, config.REFERENCE_CATALOG, None)
        self._register(reference_manager=ct)
        self._updateCatalog(container)

    def manage_afterClone(self, item):
        """
        Get a new UID (effectivly dropping reference)
        (Called when the object is cloned.)
        """
        uc = getToolByName(self, config.UID_CATALOG)

        if not hasattr(self,config.UUID_ATTR) or len(uc(UID=self.UID())):
            #if the object has no UID or the UID already exists, get a new one
            setattr(self, config.UUID_ATTR, None)

        self._register()
        self._updateCatalog(self)

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
    def _catalogUID(self, aq, uc=None):
        if not uc:
            uc = getToolByName(aq, config.UID_CATALOG)
        url = getRelURL(aq, self.getPhysicalPath())
        uc.catalog_object(self, url)

    def _uncatalogUID(self, aq, uc=None):
        if not uc:
            uc = getToolByName(aq, config.UID_CATALOG)
        url = getRelURL(aq, self.getPhysicalPath())
        uc.uncatalog_object(url)

    def _catalogRefs(self, aq, uc=None, rc=None, ignoreExceptions=1):
        annotations = self._getReferenceAnnotations()
        if annotations:
            if not uc:
                uc = getToolByName(aq, config.UID_CATALOG)
            if not rc:
                rc = getToolByName(aq, config.REFERENCE_CATALOG)
            for ref in annotations.objectValues():
                url = '/'.join(ref.getPhysicalPath())
                uc.catalog_object(ref, url)
                try:
                    rc.catalog_object(ref, url)
                except AttributeError:
                    #the AttributeError occurs after importing from a .zexp
                    #file when at the moment of this call the target object has 
                    #not yet been imported
                    #for this case the restoring of references will happen in
                    #a seperate run in the manage_afterAdd of BaseObject
                    if not ignoreExceptions:
                        raise

    def _uncatalogRefs(self, aq, uc=None, rc=None):
        annotations = self._getReferenceAnnotations()
        if annotations:
            if not uc:
                uc = getToolByName(aq, config.UID_CATALOG)
            if not rc:
                rc = getToolByName(aq, config.REFERENCE_CATALOG)
            for ref in annotations.objectValues():
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
