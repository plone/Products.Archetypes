from Acquisition import aq_base, aq_parent
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.History import Historical
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.PortalContent  import PortalContent
from debug import log, log_exc
from BaseObject import BaseObject
from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from I18NMixin import I18NMixin
from interfaces.base import IBaseContent
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata
from CatalogMultiplex import CatalogMultiplex

class BaseContent(BaseObject,
                  Referenceable,
                  CatalogMultiplex,
                  PortalContent,
                  Historical,
                  ExtensibleMetadata):
    """ A not-so-basic CMF Content implementation """

    __implements__ = (IBaseContent, IReferenceable, \
                      PortalContent.__implements__, \
                      IExtensibleMetadata)

    schema = BaseObject.schema + ExtensibleMetadata.schema

    isPrincipiaFolderish=0
    manage_options = PortalContent.manage_options + Historical.manage_options


    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        BaseObject.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

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
        mimetype = REQUEST.get_header('Content-Type', None)

        file = REQUEST['BODYFILE']
        data = file.read()
        file.seek(0)
        filename = REQUEST._steps[-2] #XXX fixme, use a real name

        #Marshall the data
        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.demarshall(self, data, mimetype=mimetype,
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

InitializeClass(BaseContent)


class I18NBaseContent(I18NMixin, BaseContent):
    """ override BaseContent to have I18N title and description,
    plus I18N related actions
    """

    schema = BaseContent.schema + I18NMixin.schema

    def __init__(self, *args, **kwargs):
        BaseContent.__init__(self, *args, **kwargs)
        I18NMixin.__init__(self)

InitializeClass(I18NBaseContent)

