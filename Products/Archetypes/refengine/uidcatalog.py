import os
import sys
from types import StringType, UnicodeType
import time
import urllib

from Products.Archetypes.lib.logging import log, log_exc
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
from Products.Archetypes.lib.utils import unique
from Products.Archetypes.lib.utils import make_uuid
from Products.Archetypes.lib.utils import getRelURL
from Products.Archetypes.lib.utils import getRelPath
from Products.Archetypes.lib.utils import shasattr

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

# The brains we want to use
class UIDCatalogBrains(AbstractCatalogBrain):
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

InitializeClass(UIDCatalogBrains)


class UIDBaseCatalog(PluggableCatalog):
    BASE_CLASS = UIDCatalogBrains

_marker=[]

class UIDCatalog(UniqueObject, ReferenceResolver, ZCatalog):
    """Unique id catalog
    """

    id = UID_CATALOG
    security = ClassSecurityInfo()
    __implements__ = IUIDCatalog

    manage_catalogFind = DTMLFile('catalogFind', _catalog_dtml)

    manage_options = ZCatalog.manage_options + \
        ({'label': 'Rebuild catalog',
         'action': 'manage_rebuildCatalog',}, )


    def __init__(self, id, title='', vocab_id=None, container=None):
        """We hook up the brains now"""
        ZCatalog.__init__(self, id, title, vocab_id, container)
        self._catalog = UIDBaseCatalog()

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
        self.ZopeFindAndApply(obj,
                              obj_metatypes=mt,
                              search_sub=1,
                              REQUEST=REQUEST,
                              apply_func=func,
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

def manage_addUIDCatalog(self, id, title,
                         vocab_id=None, # Deprecated
                         REQUEST=None):
    """Add the UID Catalog
    """
    id = str(id)
    title = str(title)
    c = UIDCatalog(id, title, vocab_id, self)
    self._setObject(id, c)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST,update_menu=1)
