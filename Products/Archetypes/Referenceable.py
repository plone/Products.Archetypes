from zope.interface import implementer

from plone.uuid.interfaces import IUUID

from Products.Archetypes import config
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.interfaces import IReferenceable
from Products.Archetypes.utils import shasattr, isFactoryContained

from Acquisition import aq_base, aq_parent, aq_inner
from OFS.ObjectManager import BeforeDeleteException

from Products.CMFCore.utils import getToolByName
from OFS.CopySupport import CopySource
from OFS.Folder import Folder
from utils import getRelURL

from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

####
# In the case of:
# - a copy:
# * we want to lose refs on the new object
# * we want to keep refs on the orig object
# - a cut/paste
# * we want to keep refs
# - a delete:
# * to lose refs
####


@implementer(IReferenceable)
class Referenceable(CopySource):
    """ A Mix-in for Referenceable objects """
    isReferenceable = 1

    security = ClassSecurityInfo()
    # Note: methods of this class are made non-publishable by not giving them
    # docstrings.

    def reference_url(self):
        # like absoluteURL, but return a link to the object with this UID"""
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.reference_url(self)

    def hasRelationshipTo(self, target, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.hasRelationshipTo(self, target, relationship)

    def addReference(self, object, relationship=None, referenceClass=None,
                     updateReferences=True, **kwargs):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.addReference(self, object, relationship, referenceClass,
                                 updateReferences, **kwargs)

    def deleteReference(self, target, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.deleteReference(self, target, relationship)

    def deleteReferences(self, relationship=None):
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.deleteReferences(self, relationship)

    def getRelationships(self):
        # What kinds of relationships does this object have
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.getRelationships(self)

    def getBRelationships(self):
        # What kinds of relationships does this object have from others
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        return tool.getBackRelationships(self)

    def getRefs(self, relationship=None, targetObject=None):
        # get all the referenced objects for this object
        tool = getToolByName(self, 'reference_catalog')
        brains = tool.getReferences(self, relationship, targetObject=targetObject,
                                    objects=False)
        if brains:
            return [self._optimizedGetObject(b.targetUID) for b in brains]
        return []

    def _getURL(self):
        # the url used as the relative path based uid in the catalogs
        return getRelURL(self, self.getPhysicalPath())

    def getBRefs(self, relationship=None, targetObject=None):
        # get all the back referenced objects for this object
        tool = getToolByName(self, 'reference_catalog')
        brains = tool.getBackReferences(self, relationship,
                                        targetObject=targetObject, objects=False)
        if brains:
            return [self._optimizedGetObject(b.sourceUID) for b in brains]
        return []

    # aliases
    getReferences = getRefs
    getBackReferences = getBRefs

    def getReferenceImpl(self, relationship=None, targetObject=None):
        # get all the reference objects for this object
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getReferences(
            self, relationship, targetObject=targetObject)
        if refs:
            return refs
        return []

    def getBackReferenceImpl(self, relationship=None, targetObject=None):
        # get all the back reference objects for this object
        tool = getToolByName(self, config.REFERENCE_CATALOG)
        refs = tool.getBackReferences(
            self, relationship, targetObject=targetObject)
        if refs:
            return refs
        return []

    def _optimizedGetObject(self, uid):
        tool = getToolByName(self, 'uid_catalog', None)
        if tool is None:  # pragma: no cover
            return ''
        tool = aq_inner(tool)
        traverse = aq_parent(tool).unrestrictedTraverse

        _catalog = tool._catalog
        rids = _catalog.indexes['UID']._index.get(uid, ())
        if isinstance(rids, int):
            rids = (rids, )

        for rid in rids:
            path = _catalog.paths[rid]
            obj = traverse(path, default=None)
            if obj is not None:
                return obj

    def _register(self, reference_manager=None):
        # register with the archetype tool for a unique id
        if IUUID(self, None) is not None:
            return

        if reference_manager is None:
            reference_manager = getToolByName(self, config.REFERENCE_CATALOG)
        reference_manager.registerObject(self)

    def _unregister(self):
        # unregister with the archetype tool, remove all references
        reference_manager = getToolByName(self, config.REFERENCE_CATALOG)
        reference_manager.unregisterObject(self)

    def _getReferenceAnnotations(self):
        # given an object, extract the bag of references for which it is the
        # source
        if not getattr(aq_base(self), config.REFERENCE_ANNOTATION, None):
            setattr(self, config.REFERENCE_ANNOTATION,
                    Folder(config.REFERENCE_ANNOTATION))

        return getattr(self, config.REFERENCE_ANNOTATION).__of__(self)

    def _delReferenceAnnotations(self):
        # Removes annotation from self
        if getattr(aq_base(self), config.REFERENCE_ANNOTATION, None):
            delattr(self, config.REFERENCE_ANNOTATION)

    def UID(self):
        return IUUID(self, None)

    def _setUID(self, uid):
        old_uid = IUUID(self, None)
        if old_uid is None:
            # Nothing to be done.
            return
        # Update forward references
        fw_refs = self.getReferenceImpl()
        for ref in fw_refs:
            assert ref.sourceUID == old_uid
            ref.sourceUID = uid
            item = ref
            container = aq_parent(aq_inner(ref))
            # We call manage_afterAdd to inform the
            # reference catalog about changes.
            ref.manage_afterAdd(item, container)
        # Update back references
        back_refs = self.getBackReferenceImpl()
        for ref in back_refs:
            assert ref.targetUID == old_uid
            ref.targetUID = uid
            item = ref
            container = aq_parent(aq_inner(ref))
            # We call manage_afterAdd to inform the
            # reference catalog about changes.
            ref.manage_afterAdd(item, container)
        setattr(self, config.UUID_ATTR, uid)
        item = self
        container = aq_parent(aq_inner(item))
        # We call manage_afterAdd to inform the
        # reference catalog about changes.
        self.manage_afterAdd(item, container)

    def _updateCatalog(self, container):
        # Update catalog after copy, rename ...

        # the UID index needs to be updated for any annotations we
        # carry
        try:
            uc = getToolByName(container, config.UID_CATALOG)
        except AttributeError:
            # TODO when trying to rename or copy a whole site than
            # container is the object "under" the portal so we can
            # NEVER ever find the catalog which is bad ...
            container = aq_parent(self)
            uc = getToolByName(container, config.UID_CATALOG)

        rc = getToolByName(uc, config.REFERENCE_CATALOG)

        self._catalogUID(container, uc=uc)
        self._catalogRefs(container, uc=uc, rc=rc)

    # OFS Hooks
    def manage_afterAdd(self, item, container):
        # Get a UID
        # (Called when the object is created or moved.)

        if isFactoryContained(self):
            return
        isCopy = getattr(item, '_v_is_cp', None)
        # Before copying we take a copy of the references that are to be copied
        # on the new copy
        rfields = self.Schema().filterFields(type="reference", keepReferencesOnCopy=1)
        rrefs = {}
        if isCopy:
            # If the object is a copy of a existing object we
            # want to renew the UID, and drop all existing references
            # on the newly-created copy.
            for r in rfields:
                rrefs[r.getName()] = r.get(self)
            setattr(self, config.UUID_ATTR, None)
            self._delReferenceAnnotations()

        ct = getToolByName(container, config.REFERENCE_CATALOG, None)
        self._register(reference_manager=ct)
        self._updateCatalog(container)
        self._referenceApply('manage_afterAdd', item, container)
        # copy the references
        if isCopy:
            for r in rfields:
                r.set(self, rrefs[r.getName()])

    def manage_afterClone(self, item):
        # Get a new UID (effectivly dropping reference)
        # (Called when the object is cloned.)

        uc = getToolByName(self, config.UID_CATALOG)

        isCopy = getattr(item, '_v_is_cp', None)
        if isCopy:
            # if isCopy is True, manage_afterAdd should have assigned a
            # UID already.  Don't mess with UID anymore.
            return

        # TODO Should we ever get here after the isCopy flag addition??
        # If the object has no UID or the UID already exists, then
        # we should get a new one

        uuid = IUUID(self, None)

        if (uuid is None or
                len(uc(UID=uuid))):
            setattr(self, config.UUID_ATTR, None)

        self._register()
        self._updateCatalog(self)

    def manage_beforeDelete(self, item, container):
        # Remove self from the catalog.
        # (Called when the object is deleted or moved.)

        # Change this to be "item", this is the root of this recursive
        # chain and it will be flagged in the correct mode
        storeRefs = getattr(item, '_v_cp_refs', None)
        if storeRefs is None:
            # The object is really going away, we want to remove
            # its references
            rc = getToolByName(self, config.REFERENCE_CATALOG)
            references = rc.getReferences(self)
            back_references = rc.getBackReferences(self)
            try:
                # First check the 'delete cascade' case
                if references:
                    for ref in references:
                        ref.beforeSourceDeleteInformTarget()
                # Then check the 'holding/ref count' case
                if back_references:
                    for ref in back_references:
                        ref.beforeTargetDeleteInformSource()
                # If nothing prevented it, remove all the refs
                self.deleteReferences()
            except ReferenceException, E:
                raise BeforeDeleteException(E)

        self._referenceApply('manage_beforeDelete', item, container)

        # Track the UUID
        # The object has either gone away, moved or is being
        # renamed, we still need to remove all UID/child refs
        self._uncatalogUID(container)
        self._uncatalogRefs(container)

    # Catalog Helper methods
    def _catalogUID(self, aq, uc=None):
        if not uc:
            uc = getToolByName(aq, config.UID_CATALOG)
        url = self._getURL()
        uc.catalog_object(self, url)

    def _uncatalogUID(self, aq, uc=None):
        if isFactoryContained(self):
            return
        if not uc:
            uc = getToolByName(self, config.UID_CATALOG)
        url = self._getURL()
        # XXX This is an ugly workaround. This method shouldn't be called
        # twice for an object in the first place, so we don't have to check
        # if it is still cataloged.
        rid = uc.getrid(url)
        if rid is not None:
            uc.uncatalog_object(url)

    def _catalogRefs(self, aq, uc=None, rc=None):
        annotations = self._getReferenceAnnotations()
        if annotations:
            if not uc:
                uc = getToolByName(aq, config.UID_CATALOG)
            if not rc:
                rc = getToolByName(aq, config.REFERENCE_CATALOG)
            for ref in annotations.objectValues():
                url = getRelURL(uc, ref.getPhysicalPath())
                uc.catalog_object(ref, url)
                rc.catalog_object(ref, url)
                ref._catalogRefs(uc, uc, rc)

    def _uncatalogRefs(self, aq, uc=None, rc=None):
        if isFactoryContained(self):
            return
        annotations = self._getReferenceAnnotations()
        if annotations:
            if not uc:
                uc = getToolByName(self, config.UID_CATALOG)
            if not rc:
                rc = getToolByName(self, config.REFERENCE_CATALOG)
            for ref in annotations.objectValues():
                url = getRelURL(uc, ref.getPhysicalPath())
                # XXX This is an ugly workaround. This method shouldn't be
                # called twice for an object in the first place, so we don't
                # have to check if it is still cataloged.
                uc_rid = uc.getrid(url)
                if uc_rid is not None:
                    uc.uncatalog_object(url)
                rc_rid = rc.getrid(url)
                if rc_rid is not None:
                    rc.uncatalog_object(url)

    def _getCopy(self, container):
        # We only set the '_v_is_cp' flag here if it was already set.
        #
        # _getCopy gets called after _notifyOfCopyTo, which should set
        # _v_cp_refs appropriatedly.
        #
        # _getCopy is also called from WebDAV MOVE (though not from
        # 'manage_pasteObjects')
        is_cp_flag = getattr(self, '_v_is_cp', None)
        cp_refs_flag = getattr(self, '_v_cp_refs', None)
        ob = CopySource._getCopy(self, container)
        if is_cp_flag:
            setattr(ob, '_v_is_cp', is_cp_flag)
        if cp_refs_flag:
            setattr(ob, '_v_cp_refs', cp_refs_flag)
        return ob

    def _notifyOfCopyTo(self, container, op=0):
        """keep reference info internally when op == 1 (move)
        because in those cases we need to keep refs"""
        # This isn't really safe for concurrent usage, but the
        # worse case is not that bad and could be fixed with a reindex
        # on the archetype tool
        if op == 1:
            self._v_cp_refs = 1
            self._v_is_cp = 0
        if op == 0:
            self._v_cp_refs = 0
            self._v_is_cp = 1

    # Recursion Mgmt
    def _referenceApply(self, methodName, *args, **kwargs):
        # We always apply commands to our reference children
        # and if we are folderish we need to get those too
        # where as references are concerned
        children = []
        if shasattr(self, 'objectValues'):
            # Only apply to objects that subclass
            # from Referenceable, and only apply the
            # method from Referenceable. Otherwise manage_* will get
            # called multiple times.
            nc = lambda obj: isinstance(obj, Referenceable)
            children.extend(filter(nc, self.objectValues()))
        children.extend(self._getReferenceAnnotations().objectValues())
        if children:
            for child in children:
                if shasattr(Referenceable, methodName):
                    method = getattr(Referenceable, methodName)
                    method(*((child,) + args), **kwargs)

InitializeClass(Referenceable)
