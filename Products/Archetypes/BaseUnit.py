from types import StringType

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.config import *

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.Image import File
from Products.CMFCore import CMFCorePermissions
from Products.MimetypesRegistry.common import getToolByName
from Products.PortalTransforms.interfaces import idatastream
#from Products.MimetypesRegistry.mime_types import text_plain, \
#     application_octet_stream
from webdav.WriteLockInterface import WriteLockInterface

class BaseUnit(File):
    __implements__ = WriteLockInterface, IBaseUnit
    isUnit = 1

    security = ClassSecurityInfo()

    def __init__(self, name, file='', instance=None, **kw):
        self.id = self.__name__ = name
        self.update(file, instance, **kw)

    def update(self, data, instance, **kw):
        #Convert from str to unicode as needed
        mimetype = kw.get('mimetype', None)
        filename = kw.get('filename', None)
        encoding = kw.get('encoding', None)

        adapter = getToolByName(instance, 'mimetypes_registry')
        data, filename, mimetype = adapter(data, **kw)

        assert mimetype
        self.mimetype = mimetype
        if not mimetype.binary:
            assert type(data) is type(u'')
            if encoding is None:
                try:
                    encoding = adapter.guess_encoding(data)
                except UnboundLocalError:
                    # adapter is not defined, we are in object creation
                    import site
                    encoding = site.encoding
            self.original_encoding = encoding
        else:
            self.original_encoding = None
        self.raw  = data
        self.size = len(data)
        # taking care of stupid IE
        self.setFilename(filename)

    def transform(self, instance, mt):
        """Takes a mimetype so object.foo.transform('text/plain') should return
        a plain text version of the raw content

        return None if no data or if data is untranformable to desired output
        mime type
        """
        encoding = self.original_encoding
        orig = self.getRaw(encoding)
        if not orig:
            return None

        #on ZODB Transaction commit there is by specification
        #no acquisition context. If it is not present, take
        #the untransformed getRaw, this is necessary for
        #being used with APE
        if not hasattr(instance, 'aq_parent'):
            return orig

        transformer = getToolByName(instance, 'portal_transforms')
        data = transformer.convertTo(mt, orig, object=self, usedby=self.id,
                                     mimetype=self.mimetype,
                                     filename=self.filename)

        if data:
            assert idatastream.isImplementedBy(data)
            _data = data.getData()
            instance.addSubObjects(data.getSubObjects())
            portal_encoding = self.portalEncoding(instance)
            encoding = data.getMetadata().get("encoding") or encoding \
                       or portal_encoding
            if portal_encoding != encoding:
                _data = unicode(_data, encoding).encode(portal_encoding)
            return _data

        # we have not been able to transform data
        # return the raw data if it's not binary data
        # FIXME: is this really the behaviour we want ?
        if not self.isBinary():
            portal_encoding = self.portalEncoding(instance)
            if portal_encoding != encoding:
                orig = self.getRaw(portal_encoding)
            return orig

        return None

    def __str__(self):
        return self.getRaw()

    __call__ = __str__

    def __len__(self):
        return self.get_size()

    def isBinary(self):
        """return true if this contains a binary value, else false"""
        try:
            return self.mimetype.binary
        except AttributeError:
            # FIXME: backward compat, self.mimetype should not be None anymore
            return 1

    # File handling
    def get_size(self):
        return self.size

    def getRaw(self, encoding=None, instance=None):
        """return encoded raw value"""
        if self.isBinary():
            return self.raw
        # FIXME: backward compat, non binary data
        # should always be stored as unicode
        if not type(self.raw) is type(u''):
            return self.raw
        if encoding is None:
            if instance is None:
                encoding ='UTF-8'
            else:
                # FIXME: fallback to portal encoding or original encoding ?
                encoding = self.portalEncoding(instance)
        return self.raw.encode(encoding)

    def portalEncoding(self, instance):
        """return the default portal encoding, using an external python script
        (look the archetypes skin directory for the default implementation)
        """
        try:
            return instance.getCharset()
        except AttributeError:
            # that occurs during object initialization
            # (no acquisition wrapper)
            return 'UTF8'

    def getContentType(self):
        """return the imimetype object for this BU"""
        return self.mimetype

    def setContentType(self, value):
        """
        """
        #print value, self.getContentType()
        self.mimetype = value

    def content_type(self):
        return self.getContentType()

    def getFilename(self):
        return self.filename

    def setFilename(self, filename):
        """
        """
        if type(filename) is StringType:
            self.filename = filename.split("\\")[-1]
        else:
            self.filename = filename

    ### index_html
    security.declareProtected(CMFCorePermissions.View, "index_html")
    def index_html(self, REQUEST, RESPONSE):
        """download method"""
        filename = self.filename
        if self.filename:
            #print self.filename
            RESPONSE.setHeader('Content-Disposition',
                               'attachment; filename=%s' % self.getFilename())
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())

        RESPONSE.write(self.getRaw(encoding=self.original_encoding))
        return ''

    ### webDAV me this, webDAV me that
    security.declareProtected( CMFCorePermissions.ModifyPortalContent, 'PUT' )
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        mimetype=REQUEST.get_header('Content-Type', None)

        file=REQUEST['BODYFILE']
        data = file.read()

        self.update(data, self.aq_parent, mimetype=mimetype)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self, REQUEST, RESPONSE):
        "Get the raw content for this unit(also used for the WebDAV SRC)"
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())
        return self.getRaw(encoding=self.original_encoding)

InitializeClass(BaseUnit)

# Backward-compatibility. Should eventually go away after 1.3-final.
newBaseUnit = BaseUnit
