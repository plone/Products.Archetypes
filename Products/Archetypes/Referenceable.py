from Acquisition import aq_base, aq_chain
from AccessControl import getSecurityManager,Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.CMFCore import CMFCorePermissions

from ExtensionClass import Base
from OFS.ObjectManager import BeforeDeleteException
from exceptions import ReferenceException

import config
from debug import log, log_exc

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

    def manage_afterClone(self, item):
        """
        Get a new UID (effectivly dropping reference)
        (Called when the object is cloned.)
        """
        setattr(self, config.UUID_ATTR, None)
        self._register()

    def manage_beforeDelete(self, item, container):
        """
            Remove self from the catalog.
            (Called when the object is deleted or moved.)
        """
        rc = getattr(container, config.REFERENCE_CATALOG)
        references = rc.getReferences(self)
        back_references = rc.getBackReferences(self)

        storeRefs = getattr(self, '_cp_refs', None)
        if storeRefs is None:
            try:
                #First check the 'delete cascade' case
                if references:
                    for ref in references:
                        ref.beforeSourceDeleteInformTarget()
                #Then check the 'holding/ref count' case
                if back_references:
                    for ref in back_references:
                        ref.beforeTargetDeleteInformSource()

                self._unregister()
            except ReferenceException, E:
                raise BeforeDeleteException(E)

        #and reset the flag
        self._cp_refs = None

    def _notifyOfCopyTo(self, container, op=0):
        """keep reference info internally when op == 1 (move)
        because in those cases we need to keep refs"""
        ## This isn't really safe for concurrent usage, but the
        ## worse case is not that bad and could be fixed with a reindex
        ## on the archetype tool
        if op==1: self._cp_refs =  1
