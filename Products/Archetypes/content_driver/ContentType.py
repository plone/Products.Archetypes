from AccessControl import ClassSecurityInfo
from Products.Archetypes.debug import log
from Globals import InitializeClass
import os.path

class ContentType:
    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    def __init__(self, name,
                 mime_types=None,
                 extensions=None,
                 binary=0,
                 icon="document_icon.gif"):
        if not mime_types: mime_types = []
        if not extensions: extensions = []

        self.name = name
        self.mime_types = mime_types
        self.extensions = extensions
        self.binary = binary
        self.icon   = icon

    def getConverter(self):
        return getConverter(self.getMimeType())

    def isBinary(self):
        return getattr(self, 'binary', 0)

    def getIcon(self):
        return getattr(self, 'icon', 'document_icon.gif')

    def getMimeType(self):
        return self.mime_types[0]

    def __cmp__(self, mime_type):
        return mime_type in self.mime_types

    def __str__(self):
        return self.getMimeType()

    def __repr__(self):
        return "<ContentType: %s %s>" % (self.name, self.getMimeType())

InitializeClass(ContentType)

class ContentTypeManager:
    def __init__(self, content_types=()):
        self.extensions = {}
        self.mime_types  = {}
        self.converters = {}

        #We mark the last one in the list as the default
        self.default = None
        if len(content_types): self.default = content_types[-1]

        self.process_types(content_types)

    def addType(self, content_type, default=0):
        for ext in content_type.extensions:
            self.extensions[ext] = content_type

        for mt in content_type.mime_types:
            self.mime_types[mt] = content_type

        if default == 1:
            self.default = content_type

    def process_types(self, content_types):
        for ct in content_types:
            self.addType(ct)

    def getByExtension(self, ext):
        return self.extensions.get(ext, self.default)

    def getByMimeType(self, mime_type):
        value = self.mime_types.get(mime_type)
        if value is None and mime_type:
            mime_type = mime_type[:mime_type.find('/')] + "/*"

        if value is None:
            value = self.mime_types.get(mime_type, None)
        return value

    def getDefault(self):
        default = self.default
        if not default:
            log("No default ContentType set?")
        return self.default

    def bind(self, content_type, converterKlass):
        self.converters[str(content_type)] = converterKlass

    def getConverter(self, content_type):
        klass = self.converters.get(str(content_type))
        if callable(klass):
            klass = klass()
        return klass


    def associateConverter(self, converter, content_type=None):
        if not content_type:
            content_type = self.mime_types.get(converter.mime_type)
            if not content_type:
                log("No Converter for %s" % mime_type)
                return

        valid = converter.initialize(content_type)
        if not valid: return

        self.bind(content_type, converter.__class__)




_ctm = ContentTypeManager()

def registerConverter(converter, content_type):
    _ctm.associateConverter(converter, content_type=content_type)

def addContentType(ct, default=0):
    _ctm.addType(ct, default)
    return ct

def selectPlugin(file='', mimetype=''):
    ''' Find a converter for 'file'.
        If 'file' is type(file), get 'mimetype' from 'file.headers',
        otherwise try getting a plugin from the file extension,
        otherwise use the passed-in 'mimetype',
        otherwise return the plugin for the default content-type.
    '''
    if file and (type(file) is not type('')):
        headers = getattr(file, 'headers', None)
        if headers and headers.has_key('content-type'):
            plugin = _ctm.getByMimeType(headers['content-type'])
            if plugin: return plugin

    filename = getattr(file, 'filename', '')
    ext = os.path.splitext(filename)[1]
    if file and filename:
        return _ctm.getByExtension(ext)

    return _ctm.getByMimeType(mimetype) or _ctm.getDefault()

def getDefaultPlugin(file='', mimetype=''):
    return _ctm.getDefault()

def lookupContentType(string):
    """Make an attempt to find a ContentType object for the predicate passed in
    if string begins with a '.' we look for an extension
    if it contains a '/' we check mime-types
    """
    ct = None
    if string.startswith('.'):
        ct =  _ctm.getByExtension(string[1:])
    elif '/' in string:
        ct =  _ctm.getByMimeType(string)

    return ct or _ctm.getDefault()

def getConverter(content_type):
    return _ctm.getConverter(content_type)
