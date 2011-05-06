import os.path
from zope.interface import implements

from Products.Archetypes.interfaces import IBaseUnit
from Products.Archetypes.config import *
from Products.Archetypes.log import log
from Products.Archetypes.utils import shasattr
from logging import ERROR

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.Image import File
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.interfaces import IMimetype
from webdav.interfaces import IWriteLock

_marker = []

class BaseUnit(File):
    implements(IBaseUnit, IWriteLock)

    isUnit = 1
    mimetype = None
    binary = None
    original_encoding = None
    raw = None
    size = None
    filename = None

    security = ClassSecurityInfo()

    def __init__(self, name, file='', instance=None, **kw):
        self.id = self.__name__ = name
        self.update(file, instance, **kw)

    def __setstate__(self, dict):
        mimetype = dict.get('mimetype', None)
        if IMimetype.providedBy(mimetype):
            dict['mimetype'] = str(mimetype)
            dict['binary'] = not not mimetype.binary
        File.__setstate__(self, dict)

    def update(self, data, instance, **kw):
        #Convert from str to unicode as needed
        mimetype = kw.get('mimetype', None)
        filename = kw.get('filename', None)
        encoding = kw.get('encoding', None)
        context  = kw.get('context', instance)

        adapter = getToolByName(context, 'mimetypes_registry')
        data, filename, mimetype = adapter(data, **kw)

        if self.mimetype != str(mimetype):
            self.mimetype = str(mimetype)
        if self.binary != mimetype.binary:
            self.binary = mimetype.binary
        if not self.isBinary():
            if encoding is None:
                try:
                    encoding = adapter.guess_encoding(data)
                except UnboundLocalError:
                    # adapter is not defined, we are in object creation
                    import site
                    encoding = site.encoding
            if self.original_encoding != encoding:
                self.original_encoding = encoding
        else:
            if self.original_encoding != encoding:
                self.original_encoding = None
        if type(self.raw) != type(data) or self.raw != data:
            self.raw = data
            self.size = len(data)
        # taking care of stupid IE
        self.setFilename(filename)
        self._cacheExpire()

    def transform(self, instance, mt, **kwargs):
        """Takes a mimetype so object.foo.transform('text/plain') should return
        a plain text version of the raw content

        return None if no data or if data is untranformable to desired output
        mime type
        """
        encoding = self.original_encoding
        orig = self.getRaw(encoding, instance)
        if not orig:
            return None

        #on ZODB Transaction commit there is by specification
        #no acquisition context. If it is not present, take
        #the untransformed getRaw, this is necessary for
        #being used with APE
        # Also don't break if transform was applied with a stale instance
        # from the catalog while rebuilding the catalog
        if not getattr(instance, 'aq_parent', None) is not None:
            return orig

        transformer = getToolByName(instance, 'portal_transforms')
        data = transformer.convertTo(mt, orig, object=self, usedby=self.id,
                                     context=instance,
                                     mimetype=self.mimetype,
                                     filename=self.filename)

        if data:
            _data = data.getData()
            instance.addSubObjects(data.getSubObjects())
            portal_encoding = kwargs.get('encoding',None) or \
	                      self.portalEncoding(instance)
            encoding = data.getMetadata().get("encoding") or encoding \
                       or portal_encoding
            if portal_encoding != encoding:
                _data = unicode(_data, encoding).encode(portal_encoding)
            return _data

        # we have not been able to transform data
        # return the raw data if it's not binary data
        # FIXME: is this really the behaviour we want ?
        if not self.isBinary():
            portal_encoding = kwargs.get('encoding',None) or \
	                      self.portalEncoding(instance)
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
        """Return true if this contains a binary value, else false.
        """
        try:
            return self.binary
        except AttributeError:
            # XXX workaround for "[ 1040514 ] AttributeError on some types after
            # migration 1.2.4rc5->1.3.0"
            # Somehow and sometimes the binary attribute gets lost magically
            self.binary = not str(self.mimetype).startswith('text')
            log("BaseUnit: Failed to access attribute binary for mimetype %s. "
                "Setting binary to %s" % (self.mimetype, self.binary),
                level=ERROR)
            return self.binary

    # File handling
    def get_size(self):
        """Return the file size.
        """
        return self.size

    def getRaw(self, encoding=None, instance=None):
        """Return the file encoded raw value.
        """
        if self.isBinary() or not isinstance(self.raw, unicode):
            return self.raw
        if encoding is None:
            if instance is None:
                encoding ='utf-8'
            else:
                # FIXME: fallback to portal encoding or original encoding ?
                encoding = self.portalEncoding(instance)
        return self.raw.encode(encoding)

    def portalEncoding(self, instance):
        """Return the default portal encoding, using an external python script.

        Look the archetypes skin directory for the default implementation.
        """
        try:
            return instance.getCharset()
        except AttributeError:
            # that occurs during object initialization
            # (no acquisition wrapper)
            return 'utf-8'

    def getContentType(self):
        """Return the file mimetype string.
        """
        return self.mimetype

    # Backward compatibility
    content_type = getContentType

    def setContentType(self, instance, value):
        """Set the file mimetype string.
        """
        mtr = getToolByName(instance, 'mimetypes_registry')
        result = mtr.lookup(value)
        if not result:
            raise ValueError('Unknown mime type %s' % value)
        mimetype = result[0]
        if self.mimetype != str(mimetype):
            self.mimetype = str(mimetype)
        if self.binary != mimetype.binary:
            self.binary = mimetype.binary
        self._cacheExpire()

    def getFilename(self):
        """Return the file name.
        """
        return self.filename

    def setFilename(self, filename):
        """Set the file name.
        """
        if isinstance(filename, str):
            filename = os.path.basename(filename)
            filename = filename.split("\\")[-1]
            if self.filename != filename:
                self.filename = filename
        else:
            if self.filename != filename:
                self.filename = filename
        self._cacheExpire()

    def _cacheExpire(self):
        if shasattr(self, '_v_transform_cache'):
            delattr(self, '_v_transform_cache')

    ### index_html
    security.declareProtected(permissions.View, "index_html")
    def index_html(self, REQUEST, RESPONSE):
        """download method"""
        filename = self.getFilename()
        if filename:
            RESPONSE.setHeader('Content-Disposition',
                               'attachment; filename=%s' % filename)
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())

        RESPONSE.write(self.getRaw(encoding=self.original_encoding))
        return ''

    ### webDAV me this, webDAV me that
    security.declareProtected( permissions.ModifyPortalContent, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        mimetype=REQUEST.get_header('Content-Type', None)

        file = REQUEST.get('BODYFILE', _marker)
        if file is _marker:
            data = REQUEST.get('BODY', _marker)
            if data is _marker:
                raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
        else:
            data = file.read()
            file.seek(0)

        self.update(data, self.aq_parent, mimetype=mimetype)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self, REQUEST, RESPONSE):
        """Get the raw content for this unit.

        Also used for the WebDAV SRC.
        """
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())
        return self.getRaw(encoding=self.original_encoding)

InitializeClass(BaseUnit)
