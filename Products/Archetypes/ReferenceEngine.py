import os
from types import StringType, UnicodeType
import time
import urllib
from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces import IContentReference
from Products.Archetypes.interfaces import IReference
from Products.Archetypes.interfaces import IReferenceCatalog

from Products.Archetypes.utils import make_uuid, getRelURL, shasattr
from Products.Archetypes.config import (
    TOOL_NAME, UID_CATALOG, REFERENCE_CATALOG, UUID_ATTR)
from Products.Archetypes.exceptions import ReferenceException

from Acquisition import aq_base, aq_parent
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Persistence import PersistentMapping
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore import permissions
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Catalog import Catalog
from Products.ZCatalog.Lazy import LazyMap
from Products import CMFCore

from plone.uuid.interfaces import IUUID

_www = os.path.join(os.path.dirname(__file__), 'www')
_catalog_dtml = os.path.join(os.path.dirname(CMFCore.__file__), 'dtml')

STRING_TYPES = (StringType, UnicodeType)

from Referenceable import Referenceable
from UIDCatalog import UIDCatalogBrains
from UIDCatalog import UIDResolver

class Reference(Referenceable, SimpleItem):
    ## Added base level support for referencing References
    ## They respond to the UUID protocols, but are not
    ## catalog aware. This means that you can't move/rename
    ## reference objects and expect them to work, but you can't
    ## do this anyway. However they should fine the correct
    ## events when they are added/deleted, etc

    implements(IReference)

    security = ClassSecurityInfo()
    portal_type = 'Reference'
    meta_type = 'Reference'

    # XXX FIXME more security

    manage_options = (
        (
        {'label':'View', 'action':'manage_view',
         },
        )+
        SimpleItem.manage_options
        )

    security.declareProtected(permissions.ManagePortal,
                              'manage_view')
    manage_view = PageTemplateFile('view_reference', _www)

    def __init__(self, id, sid, tid, relationship, **kwargs):
        self.id = id
        setattr(self, UUID_ATTR,  id)

        self.sourceUID = sid
        self.targetUID = tid
        self.relationship = relationship

        self.__dict__.update(kwargs)

    def __repr__(self):
        return "<Reference sid:%s tid:%s rel:%s>" %(self.sourceUID, self.targetUID, self.relationship)

    def UID(self):
        """the uid method for compat"""
        return IUUID(self, None)

    # Convenience methods

    def getSourceObject(self):
        return self._optimizedGetObject(self.sourceUID)

    def getTargetObject(self):
        return self._optimizedGetObject(self.targetUID)

    # Catalog support

    def targetId(self):
        target = self.getTargetObject()
        if target is not None:
            return target.getId()
        return ''

    def targetTitle(self):
        target = self.getTargetObject()
        if target is not None:
            return target.Title()
        return ''

    def Type(self):
        return self.__class__.__name__

    ###
    # Policy hooks, subclass away
    def addHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the reference being added raise a ReferenceException
        pass

    def delHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the delete raise a ReferenceException
        pass

    ###
    # OFS Operations Policy Hooks
    # These Hooks are experimental and subject to change
    def beforeTargetDeleteInformSource(self):
        """called before target object is deleted so
        the source can have a say"""
        pass

    def beforeSourceDeleteInformTarget(self):
        """called when the refering source Object is
        about to be deleted"""
        pass

    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)

        # when copying a full site containe is the container of the plone site
        # and item is the plone site (at least for objects in portal root)
        base = container
        rc = getToolByName(container, REFERENCE_CATALOG)
        url = getRelURL(base, self.getPhysicalPath())
        rc.catalog_object(self, url)

    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        rc  = getToolByName(container, REFERENCE_CATALOG)
        url = getRelURL(container, self.getPhysicalPath())
        rc.uncatalog_object(url)

InitializeClass(Reference)

REFERENCE_CONTENT_INSTANCE_NAME = 'content'

class ContentReference(ObjectManager, Reference):
    '''Subclass of Reference to support contentish objects inside references '''

    implements(IContentReference)

    def __init__(self, *args, **kw):
        Reference.__init__(self, *args, **kw)


    security = ClassSecurityInfo()
    # XXX FIXME more security

    def addHook(self, *args, **kw):
        # creates the content instance
        if type(self.contentType) in (type(''),type(u'')):
            # type given as string
            tt=getToolByName(self,'portal_types')
            tt.constructContent(self.contentType, self,
                                REFERENCE_CONTENT_INSTANCE_NAME)
        else:
            # type given as class
            setattr(self, REFERENCE_CONTENT_INSTANCE_NAME,
                    self.contentType(REFERENCE_CONTENT_INSTANCE_NAME))
            getattr(self, REFERENCE_CONTENT_INSTANCE_NAME)._md=PersistentMapping()

    def delHook(self, *args, **kw):
        # remove the content instance
        if type(self.contentType) in (type(''),type(u'')):
            # type given as string
            self._delObject(REFERENCE_CONTENT_INSTANCE_NAME)
        else:
            # type given as class
            delattr(self, REFERENCE_CONTENT_INSTANCE_NAME)

    def getContentObject(self):
        return getattr(self.aq_inner.aq_explicit, REFERENCE_CONTENT_INSTANCE_NAME)

    def manage_afterAdd(self, item, container):
        Reference.manage_afterAdd(self, item, container)
        ObjectManager.manage_afterAdd(self, item, container)

    def manage_beforeDelete(self, item, container):
        ObjectManager.manage_beforeDelete(self, item, container)
        Reference.manage_beforeDelete(self, item, container)

InitializeClass(ContentReference)

class ContentReferenceCreator:
    '''Helper class to construct ContentReference instances based
       on a certain content type '''

    security = ClassSecurityInfo()

    def __init__(self,contentType):
        self.contentType=contentType

    def __call__(self,*args,**kw):
        #simulates the constructor call to the reference class in addReference
        res=ContentReference(*args,**kw)
        res.contentType=self.contentType

        return res

InitializeClass(ContentReferenceCreator)

# The brains we want to use

class ReferenceCatalogBrains(UIDCatalogBrains):
    pass


class PluggableCatalog(Catalog):
    # Catalog overrides
    # smarter brains, squirrely traversal

    security = ClassSecurityInfo()
    # XXX FIXME more security

    def useBrains(self, brains):
        """Tricky brains overrides, we need to use our own class here
        with annotation support
        """
        class plugbrains(self.BASE_CLASS, brains):
            pass

        schema = self.schema
        scopy = schema.copy()

        scopy['data_record_id_']=len(schema.keys())
        scopy['data_record_score_']=len(schema.keys())+1
        scopy['data_record_normalized_score_']=len(schema.keys())+2

        plugbrains.__record_schema__ = scopy

        self._v_brains = brains
        self._v_result_class = plugbrains

InitializeClass(PluggableCatalog)

class ReferenceBaseCatalog(PluggableCatalog):
    BASE_CLASS = ReferenceCatalogBrains


class IndexableObjectWrapper(object):
    """Wwrapper for object indexing
    """
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return getattr(self._obj, name)

    def Title(self):
        # TODO: dumb try to make sure UID catalog doesn't fail if Title can't be
        # converted to an ascii string
        # Title is used for sorting only, maybe we could replace it by a better
        # version
        title = self._obj.Title()
        try:
            return str(title)
        except UnicodeDecodeError:
            return self._obj.getId()


class ReferenceCatalog(UniqueObject, UIDResolver, ZCatalog):
    """Reference catalog
    """

    id = REFERENCE_CATALOG
    security = ClassSecurityInfo()
    implements(IReferenceCatalog)

    manage_catalogFind = DTMLFile('catalogFind', _catalog_dtml)
    manage_options = ZCatalog.manage_options

    def __init__(self, id, title='', vocab_id=None, container=None):
        """We hook up the brains now"""
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self._catalog = ReferenceBaseCatalog()

    ###
    ## Public API
    def addReference(self, source, target, relationship=None,
                     referenceClass=None, updateReferences=True, **kwargs):
        sID, sobj = self._uidFor(source)
        if not sID or sobj is None:
            raise ReferenceException('Invalid source UID')

        tID, tobj = self._uidFor(target)
        if not tID or tobj is None:
            raise ReferenceException('Invalid target UID')

        if updateReferences:
            objects = self._resolveBrains(
                self._queryFor(sID, tID, relationship))
            if objects:
                #we want to update the existing reference
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
        # delete all the references held by an object
        for b in self.getReferences(object, relationship):
            self._deleteReference(b)

        for b in self.getBackReferences(object, relationship):
            self._deleteReference(b)

    def getReferences(self, object, relationship=None, targetObject=None,
                      objects=True):
        # return a collection of reference objects
        return self._optimizedReferences(object, relationship=relationship,
            targetObject=targetObject, objects=objects, attribute='sourceUID')

    def getBackReferences(self, object, relationship=None, targetObject=None,
                          objects=True):
        # return a collection of reference objects

        # Back refs would be anything that target this object
        return self._optimizedReferences(object, relationship=relationship,
            targetObject=targetObject, objects=objects, attribute='targetUID')

    def _optimizedReferences(self, object, relationship=None,
        targetObject=None, objects=True, attribute='sourceUID'):

        sID, sobj = self._uidFor(object)
        if targetObject:
            tID, tobj = self._uidFor(targetObject)
            if attribute == 'sourceUID':
                brains = self._queryFor(sID, tID, relationship)
            else:
                brains = self._queryFor(tID, sID, relationship)
        else:
            brains = self._optimizedQuery(sID, attribute, relationship)

        if objects:
            return self._resolveBrains(brains)
        return brains

    def _optimizedQuery(self, uid, indexname, relationship):
        """query reference catalog for object matching the info we are
        given, returns brains
        """
        if not uid: # pragma: no cover
            return []

        _catalog = self._catalog
        indexes = _catalog.indexes

        # First get one or multiple record ids for the source/target uid index
        rids = indexes[indexname]._index.get(uid, None)
        if rids is None:
            return []
        elif isinstance(rids, int):
            rids = [rids]
        else:
            rids = list(rids)

        # As a second step make sure we only get references of the right type
        # The unindex holds data of the type: [(-311870037, 'relatesTo')]
        # The index holds data like: [('relatesTo', -311870037)]
        if relationship is None:
            result_rids = rids
        else:
            rel_unindex_get = indexes['relationship']._unindex.get
            result_rids = set()
            if isinstance(relationship, str):
                relationship = set([relationship])
            for r in rids:
                rels = rel_unindex_get(r, None)
                if rels is None:
                    rels = set()
                elif isinstance(rels, str):
                    rels = set([rels])
                if not rels.isdisjoint(relationship):
                    result_rids.add(r)

        # Create brains
        return LazyMap(_catalog.__getitem__,
                       list(result_rids), len(result_rids))

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
        # Get all relationship types this object has TO other objects
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(sid=sID)
        res = {}
        for brain in brains:
            res[brain.relationship] = 1

        return res.keys()

    def getBackRelationships(self, object):
        # Get all relationship types this object has FROM other objects
        sID, sobj = self._uidFor(object)
        brains = self._queryFor(tid=sID)
        res = {}
        for b in brains:
            res[b.relationship]=1

        return res.keys()


    def isReferenceable(self, object):
        return (IReferenceable.providedBy(object) or
                shasattr(object, 'isReferenceable'))

    def reference_url(self, object):
        # return a url to an object that will resolve by reference
        sID, sobj = self._uidFor(object)
        return "%s/lookupObject?uuid=%s" % (self.absolute_url(), sID)

    def lookupObject(self, uuid, REQUEST=None):
        # Lookup an object by its uuid
        obj = self._objectByUUID(uuid)
        if REQUEST:
            return REQUEST.RESPONSE.redirect(obj.absolute_url())
        else:
            return obj

    #####
    ## UID register/unregister
    security.declareProtected(permissions.ModifyPortalContent, 'registerObject')
    def registerObject(self, object):
        self._uidFor(object)

    security.declareProtected(permissions.ModifyPortalContent, 'unregisterObject')
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

        query = {}
        if sid: query['sourceUID'] = sid
        if tid: query['targetUID'] = tid
        if relationship: query['relationship'] = relationship
        if targetId: query['targetId'] = targetId
        brains = self.searchResults(query, merge=merge)

        return brains


    def _uidFor(self, obj):
        # We should really check for the interface but I have an idea
        # about simple annotated objects I want to play out
        if not isinstance(obj, basestring):
            uobject = aq_base(obj)
            if not self.isReferenceable(uobject):
                raise ReferenceException, "%r not referenceable" % uobject

            uuid = IUUID(uobject, None)
            if uuid is None:
                uuid = self._getUUIDFor(uobject)
                
        else:
            uuid = obj
            obj = None
            #and we look up the object
            uid_catalog = getToolByName(self, UID_CATALOG)
            brains = uid_catalog(dict(UID=uuid))
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
            try:
                annotation._delObject(IUUID(referenceObject, None))
            except (AttributeError, KeyError):
                pass

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
        if IReferenceable.providedBy(obj):
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



    security.declareProtected(permissions.ManagePortal, 'manage_catalogFoundItems')
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

    security.declareProtected(permissions.ManagePortal, 'manage_rebuildCatalog')
    def manage_rebuildCatalog(self, REQUEST=None, RESPONSE=None):
        """
        """
        elapse = time.time()
        c_elapse = time.clock()

        atool = getToolByName(self, TOOL_NAME)
        obj = aq_parent(self)
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
