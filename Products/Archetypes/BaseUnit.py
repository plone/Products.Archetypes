from AccessControl import ClassSecurityInfo
from Acquisition import Explicit
from Globals import InitializeClass
from OFS.Image import File
from OFS.ObjectManager import ObjectManager, REPLACEABLE
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from Products.PortalTransforms.interfaces import idatastream
from Products.PortalTransforms.mime_types import text_plain
from StringIO import StringIO
from content_driver import getDefaultPlugin, lookupContentType, getConverter
from content_driver import selectPlugin, lookupContentType
from debug import log, log_exc
from interfaces.base import IBaseUnit
from types import DictType
from utils import basename
from webdav.WriteLockInterface import WriteLockInterface
import os.path
import re
import urllib

INITIAL_MIMETYPE = text_plain()

from config import *

try:
    from Products.PortalTransforms.interfaces import idatastream
except ImportError:
    if USE_NEW_BASEUNIT:
        raise ImportError('The PortalTransforms package is required with new base unit')
    from interfaces.interface import Interface
    class idatastream(Interface):
        """ Dummy idatastream for when PortalTransforms isnt available """


class newBaseUnit(File):
    __implements__ = (WriteLockInterface, IBaseUnit)
    isUnit = 1

    security = ClassSecurityInfo()

    def __init__(self, name, file='', instance=None,
                 mimetype=None, encoding=None):
        self.id = name
        self.update(file, instance, mimetype, encoding)

    def update(self, data, instance, mimetype=None, encoding=None):
        #Convert from str to unicode as needed
        try:
            adapter = getToolByName(instance, 'mimetypes_registry')
        except AttributeError, e:
            # this occurs on object creation
            data = data and unicode(data) or u''
            filename = None
            mimetype = INITIAL_MIMETYPE
        else:
            data, filename, mimetype = adapter(data, mimetype=mimetype, encoding=encoding)
            
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
        self.filename = filename


    def transform(self, instance, mt):
        """Takes a mimetype so object.foo['text/plain'] should return
        a plain text version of the raw content
        """
        encoding = self.original_encoding
        orig = self.getRaw(encoding)
        transformer = getToolByName(instance, 'portal_transforms')
        data = transformer.convertTo(mt, orig, object=self, usedby=self.id,
                                     mimetype=self.mimetype,
                                     filename=self.filename)

        if data:
            assert idatastream.isImplementedBy(data)
            _data = data.getData()
            instance.addSubObjects(data.getSubObjects())
            portal_encoding = self.portalEncoding()
            if portal_encoding != encoding:
                _data = unicode(_data, encoding).encode(portal_encoding)
            return _data

        # we have not been able to transform data
        # return the raw data if it's not binary data
        # FIXME: is this really the behaviour we want ?
        if not self.isBinary():
            portal_encoding = self.portalEncoding()
            if portal_encoding != encoding:
                orig = self.getRaw(portal_encoding)
            return orig
        
        return None

    def __str__(self):
        return self.getRaw()

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

    def getRaw(self, encoding=None):
        """return encoded raw value"""
        if self.isBinary():
            return self.raw
        # FIXME: backward compat, non binary data should always be stored as unicode
        if not type(self.raw) is type(u''):
            return self.raw
        if encoding is None:
            # FIXME: fallback to portal encoding or original encoding ?
            encoding = self.portalEncoding()
        return self.raw.encode(encoding)
    
    def portalEncoding(self):
        site_props = self.portal_properties.site_properties
        return site_props.getProperty('default_charset', 'UTF-8')
    
    def getContentType(self):
        """return the imimetype object for this BU"""
        return self.mimetype

    ### index_html
    security.declareProtected(CMFCorePermissions.View, "index_html")
    def index_html(self, REQUEST, RESPONSE):
        """download method"""
        filename = self.filename
        if self.filename:
            RESPONSE.setHeader('Content-Disposition', 'attachment; filename=%s' % self.filename)
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

        self.update(data, mimetype=mimetype)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self, REQUEST, RESPONSE):
        "Get the raw content for this unit(also used for the WebDAV SRC)"
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())
        return self.getRaw(encoding=self.original_encoding)


from OFS.content_types import guess_content_type

class oldBaseUnit(File, ObjectManager):
    """ """
    security = ClassSecurityInfo()
    __replaceable__ = REPLACEABLE
    __implements__ = (WriteLockInterface, IBaseUnit)
    isUnit = 1

    def __init__(self, name, file='', instance=None, mimetype=None, encoding=None):
        self.id = name
        self.filename = ''
        self.data = ''
        self.size = 0
        self.content_type = mimetype
        self.mimetype = mimetype
        self.update(file, mimetype)

    def __str__(self):
        #This should return the default transform for the type,
        #usually HTML. Keep in mind that non-text fields don't
        #get baseunits
        return self.getHTML()

    __call__ = __str__

    def reConvert(self):
        """reconvert an existing field"""
        driver = self.content_type.getConverter()
        self._update_data(self.data, self.content_type, driver)
        self.aq_parent.reindexObject()
        return self.getHTML()

    def update(self, file, mimetype=None):
        if file and (type(file) is not type('')):
            if hasattr(file, 'filename') and file.filename != '':
                self.fullfilename = getattr(file, 'filename')
                self.filename = basename(self.fullfilename)
        # need to introduce this since field doesn't care of mime type anymore
        if mimetype is None:
            if file and hasattr(file, 'read'):
                data = file.read()
                file.seek(0)
            else:
                data = file or ''
            mimetype, enc = guess_content_type(self.filename, data, mimetype)
            self.mimetype = mimetype
        driver, mimetype = self._driverFromType(mimetype, file)

        self.content_type = mimetype
        self._update_data(file, mimetype, driver)

    def _driverFromType(self, mimetype, file=None):
        driver = None
        try:
            plugin = selectPlugin(file=file, mimetype=mimetype)
            mimetype = str(plugin)
            driver    = plugin.getConverter()
        except:
            log_exc()
            plugin = lookupContentType('text/plain')
            mimetype = str(plugin)
            driver    = plugin.getConverter()

        return driver, mimetype


    def _update_data(self, file, content_type, driver):
        # This will populate its first arg with
        # .html .text and whatever else it needs to
        # satisfy the interface
        if file and (type(file) is not type('')):
            if hasattr(file, 'read'):
                contents = file.read()
                if contents:
                    self.data = contents
                file.seek(0)
                self.size = len(self.data)
        else:
            self.data = file
            self.size = 0

        driver.convertData(self, self.data)
        if hasattr(driver, 'fixSubObjects'):
            driver.fixSubObjects("%s/" % self.id, self)

        self._p_changed = 1

    security.declarePublic('getContentType')
    def getContentType(self):
        """The content type of the unit"""
        if not self.content_type:
            self.content_type = getDefaultPlugin().getMimeType()
        elif type(self.content_type) != type(''): #Fix source of this
            self.content_type = self.content_type.getMimeType()
        return self.content_type

    def getContentObject(self):
        return lookupContentType(self.getContentType())

    security.declareProtected(CMFCorePermissions.View, 'isBinary')
    def isBinary(self):
        """Is the content displable as text"""
        return self.getContentObject().isBinary()

    security.declareProtected(CMFCorePermissions.View, "index_html")
    def index_html(self, REQUEST, RESPONSE):
        """download method"""
        RESPONSE.setHeader('Content-Disposition', 'attachment; filename=%s' % self.Filename())
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())
        return File.index_html(self, REQUEST, RESPONSE)

    security.declarePublic('Filename')
    def Filename(self):
        return getattr(self, 'filename', '')

    security.declareProtected(CMFCorePermissions.View, 'getHTML')
    def getHTML(self):
        """The HTML version of the Unit"""
        return self.html

    security.declareProtected(CMFCorePermissions.View, 'getRaw')
    def getRaw(self):
        """Raw Unaltered Content"""
        return self.data

    security.declareProtected(CMFCorePermissions.View, 'getText')
    def getText(self):
        """Strip HTML"""
        ##Strip entities too?
        text = re.sub('<[^>]*>(?i)(?m)', '', self.getHTML())
        return urllib.unquote(re.sub('\n+', '\n', text)).strip()

    #security.declareProtected(CMFCorePermissions.View, 'get_size')
    security.declarePublic("get_size")
    def get_size(self):
        """aprox size of element"""
        return self.size

    security.declarePublic("getIcon")
    def getIcon(self):
        """Icon for the content type"""
        return self.getContentObject().getIcon()

    security.declareProtected(CMFCorePermissions.View, 'SearchableText')
    def SearchableText(self):
        """Indexable text"""
        return self.getText()


    security.declareProtected( CMFCorePermissions.View, 'manage_FTPget' )
    def manage_FTPget(self, REQUEST, RESPONSE):
        "Get the raw content for this unit(also used for the WebDAV SRC)"

        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())

        data=self.data
        if type(data) is type(''): return data

        while data is not None:
            RESPONSE.write(data.data)
            data=data.next

        return ''

    security.declareProtected( CMFCorePermissions.ModifyPortalContent, 'PUT' )
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        type=REQUEST.get_header('Content-Type', None)

        file=REQUEST['BODYFILE']
        data = file.read()
        driver, mimetype = self._driverFromType(type, file)
        self._update_data(data, mimetype, driver)
        self.size = len(data)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE

if USE_NEW_BASEUNIT:
    BaseUnit = newBaseUnit
else:
    BaseUnit = oldBaseUnit

InitializeClass(BaseUnit)
