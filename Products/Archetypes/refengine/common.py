from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.ZCatalog.Catalog import Catalog
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


class RelativPathCatalogBrains(AbstractCatalogBrain):
    """fried my little brains"""

    security = ClassSecurityInfo()

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
                obj = aq_inner( obj )
            except ConflictError:
                raise
            except: #NotFound # XXX bare exception
                pass

            if not obj:
                if REQUEST is None:
                    REQUEST = self.REQUEST
                obj = self.aq_parent.resolve_url(self.getPath(), REQUEST)

            return obj
        except ConflictError:
            raise
        except:
            #import traceback
            #traceback.print_exc()
            zLOG.LOG('UIDCatalogBrains', zLOG.INFO, 'getObject raised an error',
                     error=sys.exc_info())
            pass

InitializeClass(RelativPathCatalogBrains)

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
