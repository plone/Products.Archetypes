from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.PortalContent  import PortalContent
from debug import log, log_exc
from BaseObject import BaseObject
from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from interfaces.base import IBaseContent
from interfaces.referenceable import IReferenceable

class BaseContent(BaseObject, Referenceable, PortalContent, \
                  ExtensibleMetadata):
    """ A not-so-basic CMF Content implementation """

    __implements__ = (IBaseContent, IReferenceable, PortalContent.__implements__)
    
    isPrincipiaFolderish=0
    manage_options = PortalContent.manage_options

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        BaseObject.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)

    security.declareProtected(CMFCorePermissions.View, 'getPrimaryField')
    def getPrimaryField(self):
        """The primary field is some object that responds to
        PUT/manage_FTPget events.
        """
        fields = self.Schema().filterFields(primary=1)
        if fields: return fields[0]
        return None

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, \
                              'PUT')
    def PUT(self, REQUEST, RESPONSE):
        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        mime_type=REQUEST.get_header('Content-Type', None)

        file=REQUEST['BODYFILE']
        data = file.read()

        #transformer = getToolByName(self, 'transform_tool')
        #mime_type   = transformer.classify(data, mime_type=type)

        #Marshall the data
        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshaller.demarshall(self, data, mime_type=mime_type)
        if self.demarshall_hook:
            self.demarshall_hook(ddata)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE


    security.declareProtected(CMFCorePermissions.View, 'manage_FTPget')
    def manage_FTPget(self, REQUEST, RESPONSE):
        "Get the raw content for this object (also used for the WebDAV SRC)"
        if not self.Schema().hasLayer('marshall'):
            RESPONSE.setStatus(501) # Not implemented
            return RESPONSE

        marshaller = self.Schema().getLayerImpl('marshall')
        ddata = marshall.marshall(self)
        if self.marshall_hook:
            ddata = self.marshall_hook(ddata)

        content_type, length, data = ddata

        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Length', length)

        if type(data) is type(''): return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

        return ''

InitializeClass(BaseContent)

