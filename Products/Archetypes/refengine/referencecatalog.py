import os
import sys
from types import StringType, UnicodeType
import time
import urllib

from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.referenceengine import IReference
from Products.Archetypes.interfaces.referenceengine import IContentReference
from Products.Archetypes.interfaces.referenceengine import IReferenceCatalog
from Products.Archetypes.interfaces.referenceengine import IUIDCatalog
from Products.Archetypes.refengine.pluggablecatalog import PluggableCatalog
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.config import UUID_ATTR
from Products.Archetypes.config import REFERENCE_ANNOTATION
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.refengine.referenceable import Referenceable
from Products.Archetypes.utils import unique
from Products.Archetypes.utils import make_uuid
from Products.Archetypes.utils import getRelURL
from Products.Archetypes.utils import getRelPath
from Products.Archetypes.utils import shasattr

from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from AccessControl import ClassSecurityInfo
from ExtensionClass import Base
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

from Globals import InitializeClass, DTMLFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore import CMFCorePermissions
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Catalog import Catalog
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from Products import CMFCore
from ZODB.POSException import ConflictError
import zLOG

_www = os.path.join(os.path.dirname(__file__), 'www')
_catalog_dtml = os.path.join(os.path.dirname(CMFCore.__file__), 'dtml')

class ReferenceCatalogBrains(UIDCatalogBrains):
    pass


class ReferenceResolver(Base):

    security = ClassSecurityInfo()
    # XXX FIXME more security

    def resolve_url(self, path, REQUEST):
        """Strip path prefix during resolution, This interacts with
        the default brains.getObject model and allows and fakes the
        ZCatalog protocol for traversal
        """
        parts = path.split('/')
        # XXX REF_PREFIX is undefined
        #if parts[-1].find(REF_PREFIX) == 0:
        #    path = '/'.join(parts[:-1])

        portal_object = self.portal_url.getPortalObject()

        try:
            return portal_object.unrestrictedTraverse(path)
        except KeyError:
            # ObjectManager may raise a KeyError when the object isn't there
            return None

    def catalog_object(self, obj, uid=None, **kwargs):
        """Use the relative path from the portal root as uid

        Ordinary the catalog is using the path from root towards object but we
        want only a relative path from the portal root

        Note: This method could be optimized by improving the calculation of the
              relative path like storing the portal root physical path in a
              _v_ var.
        """
        portal_path_len = getattr(aq_base(self), '_v_portal_path_len', None)

        if not portal_path_len:
            # cache the lenght of the portal path in a _v_ var
            urlTool = getToolByName(self, 'portal_url')
            portal_path = urlTool.getPortalObject().getPhysicalPath()
            portal_path_len = len(portal_path)
            self._v_portal_path_len = portal_path_len

        relpath = obj.getPhysicalPath()[portal_path_len:]
        uid = '/'.join(relpath)
        ##ZCatalog.catalog_object(self, CatalogObjectWrapper(context=self, obj=obj), uid, **kwargs)
        ZCatalog.catalog_object(self, obj, uid, **kwargs)

InitializeClass(ReferenceResolver)

class ReferenceCatalog(UniqueObject, ReferenceResolver, ZCatalog):
    """Reference catalog
    """

    id = REFERENCE_CATALOG
    security = ClassSecurityInfo()
    __implements__ = IReferenceCatalog

    manage_catalogFind = DTMLFile('catalogFind', _catalog_dtml)
    manage_options = ZCatalog.manage_options

    # XXX FIXME more security

    manage_options = ZCatalog.manage_options + \
        ({'label': 'Rebuild catalog',
         'action': 'manage_rebuildCatalog',}, )

    def __init__(self, id, title='', vocab_id=None, container=None):
        """We hook up the brains now"""
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self._catalog = ReferenceBaseCatalog()

    ###
    ## Public API
    def addReference(self, source, target, relationship=None,
                     referenceClass=None, **kwargs):
        sID, sobj = self._uidFor(source)
        if not sID or sobj is None:
            raise ReferenceException('Invalid source UID')

        tID, tobj = self._uidFor(target)
        if not tID or tobj is None:
            raise ReferenceException('Invalid target UID')

        objects = self._resolveBrains(self._queryFor(sID, tID, relationship))
        if objects:
            #we want to update the existing reference
            #XXX we might need to being a subtransaction here to
            #    do this properly, and close it later
            existing = objects[0]
            if existing:
                # We can't del off self, we now need to remove it
                # from the source objects annotation, which we have
                annotation = sobj._getReferenceAnnotations()
                annotation._delObject(existing.id)


        rID = self._makeName(sID, tID)
        if not referenceClass:
            referenceClass = Reference

        annotation = sobj._getReferenceAnnotations()

        referenceObject = referenceClass(rID, sID, tID, relationship,
                                         **kwargs)
        # Must be wrapped into annotation context, or else
        # it will get indexed *twice*, one time with the wrong path.
        referenceObject = referenceObject.__of__(annotation)
        try:
            referenceObject.addHook(self, sobj, tobj)
        except ReferenceException:
            pass
        else:
            # This should call manage_afterAdd
            annotation._setObject(rID, referenceObject)
            return referenceObject

    def deleteReference(self, source, target, relationship=None):
        sID, sobj = self._uidFor(source)
        tID, tobj = self._uidFor(target)

        objects = self._resolveBrains(self._queryFor(sID, tID, relationship))
        if objects:
            self._deleteReference(objects[0])

    def deleteReferences(self, object, relationship=None):
        """delete all the references held by an object"""
        for b in self.getReferences(object, relationship):
            self._deleteReference(b)

        for b in self.getBackReferences(object, relationship):
            self._deleteReference(b)

    def getReferences(self, object, relationship=None):
        """return a collection of reference objects"""
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID, relationship=relationship)
        return self._resolveBrains(brains)

    def getBackReferences(self, object, relationship=None):
        """return a collection of reference objects"""
        # Back refs would be anything that target this object
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(tid=sID, relationship=relationship)
        return self._resolveBrains(brains)

    def hasRelationshipTo(self, source, target, relationship):
        sID, sobj = self._uidFor(source)
        tID, tobj = self._uidFor(target)

        brains = self._queryFor(sID, tID, relationship)
        for brain in brains:
            obj = brain.getObject()
            if obj is not None:
                return True
        return False

    def getRelationships(self, object):
        """
        Get all relationship types this object has TO other objects
        """
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID)
        res = {}
        for brain in brains:
            res[brain.relationship] = 1

        return res.keys()

    def getBackRelationships(self, object):
        """
        Get all relationship types this object has FROM other objects
        """
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(tid=sID)
        res = {}
        for b in brains:
            res[b.relationship]=1

        return res.keys()


    def isReferenceable(self, object):
        return (IReferenceable.isImplementedBy(object) or
                shasattr(object, 'isReferenceable'))

    def reference_url(self, object):
        """return a url to an object that will resolve by reference"""
        sID, sobj = self._uidFor(object)
        return "%s/lookupObject?uuid=%s" % (self.absolute_url(), sID)

    def lookupObject(self, uuid, REQUEST=None):
        """Lookup an object by its uuid"""
        obj = self._objectByUUID(uuid)
        if REQUEST:
            return REQUEST.RESPONSE.redirect(obj.absolute_url())
        else:
            return obj

    #####
    ## UID register/unregister
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'registerObject')
    def registerObject(self, object):
        self._uidFor(object)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'unregisterObject')
    def unregisterObject(self, object):
        self.deleteReferences(object)
        uc = getToolByName(self, UID_CATALOG)
        uc.uncatalog_object(object._getURL())


    ######
    ## Private/Internal
    def _objectByUUID(self, uuid):
        tool = getToolByName(self, UID_CATALOG)
        brains = tool(UID=uuid)
        for brain in brains:
            obj = brain.getObject()
            if obj is not None:
                return obj
        else:
            return None

    def _queryFor(self, sid=None, tid=None, relationship=None,
                  targetId=None, merge=1):
        """query reference catalog for object matching the info we are
        given, returns brains

        Note: targetId is the actual id of the target object, not its UID
        """

        q = {}
        if sid: q['sourceUID'] = sid
        if tid: q['targetUID'] = tid
        if relationship: q['relationship'] = relationship
        if targetId: q['targetId'] = targetId
        brains = self.searchResults(q, merge=merge)

        return brains


    def _uidFor(self, obj):
        # We should really check for the interface but I have an idea
        # about simple annotated objects I want to play out
        if type(obj) not in STRING_TYPES:
            uobject = aq_base(obj)
            if not self.isReferenceable(uobject):
                raise ReferenceException, "%r not referenceable" % uobject

            # shasattr() doesn't work here
            if not getattr(aq_base(uobject), UUID_ATTR, None):
                uuid = self._getUUIDFor(uobject)
            else:
                uuid = getattr(uobject, UUID_ATTR)
        else:
            uuid = obj
            obj = None
            #and we look up the object
            uid_catalog = getToolByName(self, UID_CATALOG)
            brains = uid_catalog(UID=uuid)
            for brain in brains:
                res = brain.getObject()
                if res is not None:
                    obj = res
        return uuid, obj

    def _getUUIDFor(self, object):
        """generate and attach a new uid to the object returning it"""
        uuid = make_uuid(object.getId())
        setattr(object, UUID_ATTR, uuid)

        return uuid

    def _deleteReference(self, referenceObject):
        try:
            sobj = referenceObject.getSourceObject()
            referenceObject.delHook(self, sobj,
                                    referenceObject.getTargetObject())
        except ReferenceException:
            pass
        else:
            annotation = sobj._getReferenceAnnotations()
            annotation._delObject(referenceObject.UID())

    def _resolveBrains(self, brains):
        objects = []
        if brains:
            objects = [b.getObject() for b in brains]
            objects = [b for b in objects if b]
        return objects

    def _makeName(self, *args):
        """get a uuid"""
        name = make_uuid(*args)
        return name

    def __nonzero__(self):
        return 1

    def _catalogReferencesFor(self,obj,path):
        if IReferenceable.isImplementedBy(obj):
            obj._catalogRefs(self)

    def _catalogReferences(self,root=None,**kw):
        ''' catalogs all references, where the optional parameter 'root'
           can be used to specify the tree that has to be searched for references '''

        if not root:
            root=getToolByName(self,'portal_url').getPortalObject()

        path = '/'.join(root.getPhysicalPath())

        results = self.ZopeFindAndApply(root,
                                        search_sub=1,
                                        apply_func=self._catalogReferencesFor,
                                        apply_path=path,**kw)



    def manage_catalogFoundItems(self, REQUEST, RESPONSE, URL2, URL1,
                                 obj_metatypes=None,
                                 obj_ids=None, obj_searchterm=None,
                                 obj_expr=None, obj_mtime=None,
                                 obj_mspec=None, obj_roles=None,
                                 obj_permission=None):

        """ Find object according to search criteria and Catalog them
        """


        elapse = time.time()
        c_elapse = time.clock()

        words = 0
        obj = REQUEST.PARENTS[1]

        self._catalogReferences(obj,obj_metatypes=obj_metatypes,
                                 obj_ids=obj_ids, obj_searchterm=obj_searchterm,
                                 obj_expr=obj_expr, obj_mtime=obj_mtime,
                                 obj_mspec=obj_mspec, obj_roles=obj_roles,
                                 obj_permission=obj_permission)

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse

        RESPONSE.redirect(
            URL1 +
            '/manage_catalogView?manage_tabs_message=' +
            urllib.quote('Catalog Updated\n'
                         'Total time: %s\n'
                         'Total CPU time: %s'
                         % (`elapse`, `c_elapse`))
            )

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_rebuildCatalog')
    def manage_rebuildCatalog(self, REQUEST=None, RESPONSE=None):
        """
        """
        elapse = time.time()
        c_elapse = time.clock()

        atool   = getToolByName(self, TOOL_NAME)
        func    = self.catalog_object
        obj     = aq_parent(self)
        path    = '/'.join(obj.getPhysicalPath())
        if not REQUEST:
            REQUEST = self.REQUEST

        # build a list of archetype meta types
        mt = tuple([typ['meta_type'] for typ in atool.listRegisteredTypes()])

        # clear the catalog
        self.manage_catalogClear()

        # find and catalog objects
        self._catalogReferences(obj,
                                obj_metatypes=mt,
                                REQUEST=REQUEST)

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse

        if RESPONSE:
            RESPONSE.redirect(
            REQUEST.URL1 +
            '/manage_catalogView?manage_tabs_message=' +
            urllib.quote('Catalog Rebuilded\n'
                         'Total time: %s\n'
                         'Total CPU time: %s'
                         % (`elapse`, `c_elapse`))
            )

InitializeClass(ReferenceCatalog)


def manage_addReferenceCatalog(self, id, title,
                               vocab_id=None, # Deprecated
                               REQUEST=None):
    """Add a ReferenceCatalog object
    """
    id=str(id)
    title=str(title)
    c=ReferenceCatalog(id, title, vocab_id, self)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST,update_menu=1)

InitializeClass(ReferenceCatalog)
