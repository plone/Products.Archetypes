from Acquisition import aq_base, aq_parent
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.History import Historical
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.PortalContent  import PortalContent
from debug import log, log_exc
from BaseObject import BaseObject
from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from interfaces.base import IBaseContent
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata
from CatalogMultiplex import CatalogMultiplex

class BaseContentMixin(BaseObject,
                       Referenceable,
                       CatalogMultiplex,
                       PortalContent,
                       Historical):
    __implements__ = (IBaseContent, IReferenceable) + PortalContent.__implements__

    isPrincipiaFolderish=0
    manage_options = PortalContent.manage_options + Historical.manage_options

    security = ClassSecurityInfo()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)
        PortalContent.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)
        PortalContent.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)
        PortalContent.manage_beforeDelete(self, item, container)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, \
                              'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """ HTTP PUT handler with marshalling support """
        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)

        file = REQUEST['BODYFILE']
        data = file.read()
        file.seek(0)
        try:
            filename = REQUEST._steps[-2] #XXX fixme, use a real name
        except:
            filename = file.filename

        #Marshall the data
        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.demarshall(self, data, mimetype=None,
                                      filename=filename)
        if hasattr(aq_base(self), 'demarshall_hook') \
           and self.demarshall_hook:
            self.demarshall_hook(ddata)

        self.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE


    security.declareProtected(CMFCorePermissions.View, 'manage_FTPget')
    def manage_FTPget(self, REQUEST, RESPONSE):
        "Get the raw content for this object (also used for the WebDAV SRC)"

        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.marshall(self)
        if hasattr(aq_base(self), 'marshall_hook') \
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
                  ExtensibleMetadata):
    """ A not-so-basic CMF Content implementation """

    __implements__ = BaseContentMixin.__implements__ + (IExtensibleMetadata,)

    schema = BaseContentMixin.schema + ExtensibleMetadata.schema

    def __init__(self, oid, **kwargs):
        BaseContentMixin.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)


InitializeClass(BaseContent)
