from AccessControl import ClassSecurityInfo
from Acquisition import Explicit
from Globals import InitializeClass
from OFS.Image import File
from OFS.ObjectManager import ObjectManager, REPLACEABLE
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
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
import site
import urllib

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

    security = ClassSecurityInfo()

    def __init__(self, name, file='', instance=None,
                 mimetype=None, encoding=site.encoding):
        self.id = name
        self.update(file, instance, mimetype, encoding)

    def update(self, data, instance,
               mimetype=None, encoding=site.encoding):
        #Convert from file/str to str/unicode as needed
        adapter = getToolByName(instance, 'mimetypes_registry')
        data, filename, mimetype = adapter(data, mimetype=mimetype, encoding=encoding)

        self.mimetype = mimetype
        self.encoding = encoding
        # XXXFIXME: data may have been translated to unicode by the adapter method
        #            why encode it here ??
        try:
            self.raw  = data and str(data) or ''
        except UnicodeError:
            self.raw = data.encode(encoding)

        self.size = len(data)
        self.filename = filename


    def transform(self, instance, mt):
        """Takes a mimetype so object.foo['text/plain'] should return
        a plain text version of the raw content
        """
        #Do we have a cached transform for this key?
        transformer = getToolByName(instance, 'portal_transforms')
        data = transformer.convertTo(mt, self.raw, object=self, usedby=self.id,
                                     mimetype=self.mimetype,
                                     filename=self.filename)

        if data:
            assert idatastream.isImplementedBy(data)
            _data = data.getData()
            instance.addSubObjects(data.getSubObjects())
            return _data

        # we have not been able to transform data
        # return the raw data if it's not binary data
        registry = getToolByName(instance, 'mimetypes_registry')
        mt = registry.lookup(mt)
        if mt and not mt[0].binary:
            return self.raw

        return None

    def __str__(self):
        return self.raw

    def isBinary(self):
        try:
            return self.getContentType().binary
        except AttributeError:
            return 1
##         registry = getToolByName('mimetypes_registry')
##         mt = registry.lookup(self.getContentType())
##         if not mt: return 1 #if we don't hear otherwise its binary
##         return mt[0].binary

    # File handling
    def get_size(self):
        return self.size

    def getRaw(self):
        return self.raw

    def getContentType(self):
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

        RESPONSE.write(self.raw)
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

        if type(self.raw) is type(''): return self.raw

        return ''


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
