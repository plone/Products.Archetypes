from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.interfaces.base import IBaseContent
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from Products.Archetypes.utils import shasattr

from Acquisition import aq_base
from Acquisition import aq_get
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.History import Historical
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.PortalContent import PortalContent
from OFS.PropertyManager import PropertyManager
from ZODB.POSException import ConflictError

_marker = []

class BaseContentMixin(CatalogMultiplex,
                    BaseObject,
                    PortalContent,
                    Historical):
    """A not-so-basic CMF Content implementation that doesn't
    include Dublin Core Metadata"""

    __implements__ = IBaseContent, IReferenceable, PortalContent.__implements__

    isPrincipiaFolderish=0
    manage_options = PortalContent.manage_options + Historical.manage_options

    security = ClassSecurityInfo()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        BaseObject.manage_afterAdd(self, item, container)
        CatalogMultiplex.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        BaseObject.manage_afterClone(self, item)
        CatalogMultiplex.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        BaseObject.manage_beforeDelete(self, item, container)
        CatalogMultiplex.manage_beforeDelete(self, item, container)

        #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
        self._at_cp_refs = None

    def _notifyOfCopyTo(self, container, op=0):
        """OFS.CopySupport notify
        """
        BaseObject._notifyOfCopyTo(self, container, op=op)
        PortalContent._notifyOfCopyTo(self, container, op=op)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'PUT')
    def PUT(self, REQUEST=None, RESPONSE=None):
        """ HTTP PUT handler with marshalling support """
        if not REQUEST:
            REQUEST = self.REQUEST
        if not RESPONSE:
            RESPONSE = REQUEST.RESPONSE
        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)

        file = REQUEST.get('BODYFILE', _marker)
        if file is _marker:
            data = REQUEST.get('BODY', _marker)
            if data is _marker:
                raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
        else:
            data = file.read()
            file.seek(0)
        
        # XXX should we maybe not accept PUT requests without a
        # content type?
        mimetype = REQUEST.get_header('content-type', None)

        try:
            filename = REQUEST._steps[-2] #XXX fixme, use a real name
        except ConflictError:
            raise
        except:
            filename = (getattr(file, 'filename', None) or
                        getattr(file, 'name', None))

        # XXX remove after we are using global services
        # use the request to find an object in the traversal hirachie that is
        # able to acquire a mimetypes_registry instance
        # This is a hack to avoid the acquisition problem on FTP/WebDAV object
        # creation
        parents = REQUEST.get('PARENTS', None)
        context = None
        if parents is not None:
            for parent in parents:
                if aq_get(parent, 'mimetypes_registry', None, 1) is not None:
                    context = parent
                    break

        # Marshall the data
        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.demarshall(self, data,
                                      mimetype=mimetype,
                                      filename=filename,
                                      REQUEST=REQUEST,
                                      RESPONSE=RESPONSE,
                                      context=context)
        if shasattr(self, 'demarshall_hook') \
           and self.demarshall_hook:
            self.demarshall_hook(ddata)

        self.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE


    security.declareProtected(CMFCorePermissions.View, 'manage_FTPget')
    def manage_FTPget(self, REQUEST=None, RESPONSE=None):
        "Get the raw content for this object (also used for the WebDAV SRC)"

        if REQUEST is None:
            REQUEST = self.REQUEST

        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE

        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.marshall(self, REQUEST=REQUEST, RESPONSE=RESPONSE)
        if shasattr(self, 'marshall_hook') \
           and self.marshall_hook:
            ddata = self.marshall_hook(ddata)

        content_type, length, data = ddata

        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Length', length)

        if type(data) is type(''): return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

InitializeClass(BaseContentMixin)

class BaseContent(BaseContentMixin,
                  ExtensibleMetadata,
                  PropertyManager):
    """A not-so-basic CMF Content implementation with Dublin Core
    Metadata included"""

    __implements__ = BaseContentMixin.__implements__, IExtensibleMetadata

    schema = BaseContentMixin.schema + ExtensibleMetadata.schema

    manage_options = BaseContentMixin.manage_options + \
        PropertyManager.manage_options

    def __init__(self, oid, **kwargs):
        BaseContentMixin.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

InitializeClass(BaseContent)


BaseSchema = BaseContent.schema

__all__ = ('BaseContent', 'BaseContentMixin', 'BaseSchema', )
