import logging
import os
import time
import urllib
from zope.interface import implementer
from zope import component
from zope import interface

from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from ZODB.POSException import ConflictError
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import manage_zcatalog_entries as ManageZCatalogEntries
from Acquisition import aq_base, aq_parent, aq_inner
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Catalog import Catalog
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from Products import CMFCore
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.interfaces import IUIDCatalog
from Products.Archetypes.utils import getRelURL
from plone.indexer.interfaces import IIndexableObject
from plone.indexer.decorator import indexer
from plone.uuid.interfaces import IUUID, IUUIDAware

_catalog_dtml = os.path.join(os.path.dirname(CMFCore.__file__), 'dtml')
logger = logging.getLogger('Archetypes')


def manage_addUIDCatalog(self, id, title,
                         vocab_id=None,  # Deprecated
                         REQUEST=None):
    """Add the UID Catalog
    """
    id = str(id)
    title = str(title)
    c = UIDCatalog(id, title, vocab_id, self)
    self._setObject(id, c)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)


class PluggableCatalog(Catalog):
    # Catalog overrides
    # smarter brains, squirrely traversal

    security = ClassSecurityInfo()
    # XXX FIXME more security

    def useBrains(self, brains):
        # Tricky brains overrides, we need to use our own class here
        # with annotation support.
        class plugbrains(self.BASE_CLASS, brains):
            pass

        schema = self.schema
        scopy = schema.copy()

        scopy['data_record_id_'] = len(schema.keys())
        scopy['data_record_score_'] = len(schema.keys()) + 1
        scopy['data_record_normalized_score_'] = len(schema.keys()) + 2

        plugbrains.__record_schema__ = scopy

        self._v_brains = brains
        self._v_result_class = plugbrains

InitializeClass(PluggableCatalog)


class UIDCatalogBrains(AbstractCatalogBrain):
    """fried my little brains"""

    security = ClassSecurityInfo()

    security.declarePrivate('getObject')

    def getObject(self, REQUEST=None):
        """
        Used to resolve UIDs into real objects. This also must be
        annotation aware. The protocol is:
        We have the path to an object. We get this object. If its
        UID is not the UID in the brains then we need to pull it
        from the reference annotation and return that object

        Thus annotation objects store the path to the source object
        """
        obj = None
        try:
            path = self.getPath()
            try:
                portal = getToolByName(self, 'portal_url').getPortalObject()
                obj = portal.unrestrictedTraverse(self.getPath())
                obj = aq_inner(obj)
            except (ConflictError, KeyboardInterrupt):
                raise
            except:  # NotFound # XXX bare exception
                pass

            if obj is None:
                if REQUEST is None:
                    REQUEST = self.REQUEST
                obj = self.aq_parent.resolve_url(self.getPath(), REQUEST)

            return obj
        except (ConflictError, KeyboardInterrupt):
            raise
        except:
            logger.log(logging.INFO,
                       'UIDCatalogBrains getObject raised an error', exc_info=True)

InitializeClass(UIDCatalogBrains)


class IndexableObjectWrapper(object):
    """Wrapper for object indexing
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
        if isinstance(title, unicode):
            return title.encode('utf-8')
        try:
            return str(title)
        except UnicodeDecodeError:
            return self._obj.getId()

_marker = []


# let rewrite Title indexer with plone.indexer
@indexer(interface.Interface, IUIDCatalog)
def Title(obj):
    title = obj.Title()
    if isinstance(title, unicode):
        return title.encode('utf-8')
    try:
        return str(title)
    except UnicodeDecodeError:
        return obj.getId()


@indexer(IUUIDAware, IUIDCatalog)
def UID_indexer(obj):
    return IUUID(obj, None)


class UIDResolver(Base):

    security = ClassSecurityInfo()

    security.declarePrivate('catalog_object')

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
        __traceback_info__ = (repr(obj), uid)
        ZCatalog.catalog_object(self, obj, uid, **kwargs)

InitializeClass(UIDResolver)


class UIDBaseCatalog(PluggableCatalog):
    BASE_CLASS = UIDCatalogBrains


@implementer(IUIDCatalog)
class UIDCatalog(UniqueObject, UIDResolver, ZCatalog):
    """Unique id catalog
    """

    id = UID_CATALOG
    security = ClassSecurityInfo()

    manage_catalogFind = DTMLFile('catalogFind', _catalog_dtml)

    def __init__(self, id, title='', vocab_id=None, container=None):
        """We hook up the brains now"""
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self._catalog = UIDBaseCatalog()

    security.declareProtected(ManageZCatalogEntries, 'catalog_object')

    def catalog_object(self, object, uid, idxs=None,
                       update_metadata=1, pghandler=None):

        if idxs is None:
            idxs = []
        w = object
        if not IIndexableObject.providedBy(object):
            # This is the CMF 2.2 compatible approach, which should be used
            # going forward
            wrapper = component.queryMultiAdapter(
                (object, self), IIndexableObject)
            if wrapper is not None:
                w = wrapper

        ZCatalog.catalog_object(self, w, uid, idxs,
                                update_metadata, pghandler=pghandler)

    def _catalogObject(self, obj, path):
        """Catalog the object. The object will be cataloged with the absolute
           path in case we don't pass the relative url.
        """
        url = getRelURL(self, obj.getPhysicalPath())
        self.catalog_object(obj, url)

    security.declareProtected(
        CMFCore.permissions.ManagePortal, 'manage_rebuildCatalog')

    def manage_rebuildCatalog(self, REQUEST=None, RESPONSE=None):
        """
        """
        elapse = time.time()
        c_elapse = time.clock()

        atool = getToolByName(self, TOOL_NAME)
        obj = aq_parent(self)
        path = '/'.join(obj.getPhysicalPath())
        if not REQUEST:
            REQUEST = self.REQUEST

        # build a list of archetype meta types
        mt = tuple([typ['meta_type'] for typ in atool.listRegisteredTypes()])

        # clear the catalog
        self.manage_catalogClear()

        # find and catalog objects
        self.ZopeFindAndApply(obj,
                              obj_metatypes=mt,
                              search_sub=1,
                              REQUEST=REQUEST,
                              apply_func=self._catalogObject,
                              apply_path=path)

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

InitializeClass(UIDCatalog)
