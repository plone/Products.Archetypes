import os
from types import UnicodeType

from transform.interfaces import implements, imimetype, isourceAdapter, imimetypes_registry
from transform.mime_types import initialize
from transform.mimetype import mimetype, MimeTypeException

from OFS.Folder import Folder
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from ZODB.PersistentMapping import PersistentMapping
from Acquisition import aq_parent
from AccessControl import ClassSecurityInfo
from Products.Archetypes.debug import log, log_exc

_www = os.path.join(os.path.dirname(__file__), 'www')

class MimeTypesTool(UniqueObject, ActionProviderBase, Folder):
    """ Archetypes tool, manage aspects of Archetype instances """

    __implements__ = (imimetypes_registry, isourceAdapter)

    id        = 'mimetypes_registry'
    meta_type = 'MimeTypes Registry'
    isPrincipiaFolderish = 1 # Show up in the ZMI

    meta_types = all_meta_types = (
        { 'name'   : 'MimeType',
            'action' : 'manage_addMimeTypeForm'},
        )

    manage_options = (
        ( { 'label'   : 'MimeTypes',
            'action' : 'manage_main'},) +
        Folder.manage_options[2:]
        )

    manage_addMimeTypeForm = PageTemplateFile('addMimeType', _www)
    manage_main = PageTemplateFile('listMimeTypes', _www)

    manage_editMimeTypeForm = PageTemplateFile('editMimeType', _www)

    security = ClassSecurityInfo()
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self):
        # Major key -> minor imimetype objects
        self._mimetypes  = PersistentMapping()
        # ext -> imimetype mapping
        self.extensions = PersistentMapping()
        self.manage_addProperty('defaultMimetype', 'text/plain', 'string')
        # initialize mime types
        initialize(self)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_delObjects')
    def manage_delObjects(self, ids, REQUEST=None):
        """ delete the selected mime types """
        for id in ids:
            self.unregister(self.lookup(id)[0])
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addMimeType')
    def manage_addMimeType(self, id, mimetypes, extensions, icon_path, binary=0,
                           REQUEST=None):
        """add a mime type to the tool"""
        mt = mimetype(id, mimetypes, extensions, binary)
        self.register(mt, icon_path)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_editMimeType')
    def manage_editMimeType(self, name, new_name, mimetypes, extensions, icon_path, binary=0,
                    REQUEST=None):
        """ edit this mime type"""
        if type(mimetypes) in (type(''), type(u'')):
            mimetypes = [mt.strip() for mt in mimetypes.split('\n') if mt.strip()]
        if type(extensions) in (type(''), type(u'')):
            extensions = [mt.strip() for mt in extensions.split('\n') if mt.strip()]
        mt = self.lookup(name)[0]
        self.unregister(mt)
        mt.__name__ = new_name
        mt.mimetypes = mimetypes
        mt.extensions = extensions
        mt.binary = binary
        mt.icon_path = icon_path
        self.register(mt, mt.icon_path)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


    security.declareProtected(CMFCorePermissions.ManagePortal, 'register')
    def register(self, mimetype, icon_path=None):
        """ register a new mimetype

        mimetype must implement imimetype
        """
        assert implements(mimetype, imimetype)
        mimetype.icon_path = icon_path or guess_icon_path(mimetype)
        for t in mimetype.mimetypes:
            major, minor = split(t)
            if not major or not minor or minor == '*':
                raise MimeTypeException('Can\'t register mime type %s' % t)
            group = self._mimetypes.setdefault(major, PersistentMapping())
            if group.has_key(minor):
                log('Warning: redefining mime type %s (%s)' % (t, mimetype.__class__))
            group[minor] = mimetype

        for e in mimetype.extensions:
            if self.extensions.has_key(e):
                log('Warning: redefining extension %s from %s to %s' % (
                    e, self.extensions[e], mimetype))
            #we don't validate fmt yet, but its ["txt", "html"]
            self.extensions[e] = mimetype


    security.declareProtected(CMFCorePermissions.ManagePortal, 'unregister')
    def unregister(self, mimetype):
        """ unregister a new mimetype

        mimetype must implement imimetype
        """
        assert implements(mimetype, imimetype)
        for t in mimetype.mimetypes:
            major, minor = split(t)
            group = self._mimetypes.get(major, {})
            if group.get(minor) == mimetype:
                del group[minor]
        for e in mimetype.extensions:
            if self.extensions.get(e) == mimetype:
                del self.extensions[e]


    security.declarePublic('mimetypes')
    def mimetypes(self):
        """ return all defined mime types """
        res = {}
        for g in self._mimetypes.values():
            for mt in g.values():
                res[mt] =1
        return res.keys()

    security.declarePublic('list_mimetypes')
    def list_mimetypes(self):
        return [str(mt) for mt in self.mimetypes()]

    security.declarePublic('lookup')
    def lookup(self, mimetypestring):
        """ return a list of mimetypes objects associated with the RFC-2046 name
            return None if no one is known.

        mimetypestring may have an empty minor part or containing a wildcard (*)
        """
        if implements(mimetypestring, imimetype):
            return (mimetypestring, )
        __traceback_info__ = (repr(mimetypestring), str(mimetypestring))
        major, minor = split(mimetypestring)
        group = self._mimetypes.get(major, {})
        if not minor or minor == '*':
            v = group.values()
        else:
            v = group.get(minor)
            if v:
                v = (v,)
            else:
                return
            # FIXME : raise an exception if not registered mime_type ?
        return tuple([m.__of__(self) for m in v])

    security.declarePublic('lookupExtension')
    def lookupExtension(self, mimetypestring):
        """ return the mimetypes object associated with the file's extension
            return None if it is not known.

        filename maybe a file name like 'content.txt' or an extension like 'rest'
        """
        if filename.find('.') != -1:
            ext = os.path.splitext(filename)[1][1:]
        else:
            ext = filename

        return self.extensions.get(ext)

    def _classifiers(self):
        return [mt for mt in self.mimetypes() if implements(mt, iclassifier)]

    security.declarePublic('classify')
    def classify(self, data, mimetype=None, filename=None):
        """Classify works as follows:
        1) you tell me the rfc-2046 name and I give you an imimetype
           object
        2) the filename includes an extension from which we can guess
           the mimetype
        3) we can optionally introspect the data
        """
        mt = None

        if mimetype:
            mt = self.lookup(mimetype)
            if mt:
                mt = mt[0]
        elif filename:
            mt = self.lookupExtension(filename)

        if not data:
            return self.lookup(self.defaultMimetype)[0]

        if not mt:
            for c in self._classifiers():
                try:
                    if c.classify(data):
                        mt = c
                        break
                except:
                    pass
        return mt

    def __call__(self, data, **kwargs):
        """ return a 3-uple (data, filename, mimetypeobject) given some raw data
        and optional paramters
        """
        filename = mt = None
        if hasattr(data, 'read'):
            data = data.read()
        if hasattr(data, 'filename'):
            filename = data.filename
        elif hasattr(data, 'name'):
            filename = data.name()

        # We need to figure out if data is binary and skip encoding if
        # it is
        mt = self.classify(data, mimetype=kwargs.get('mimetype', None),
                           filename=filename)

        if mt and not mt.binary:
            if type(data) != UnicodeType:
                encoding = kwargs.get('encoding', 'utf_8')
                data = unicode(data, encoding)

        return (data, filename, mt)


InitializeClass(MimeTypesTool)

from os.path import dirname, join, exists

ICONS_DIR = join(dirname(__file__), 'skins', 'mimetypes_icons')

def guess_icon_path(mimetype, icons_dir=ICONS_DIR, icon_ext='png'):
    if mimetype.extensions:
        for ext in mimetype.extensions:
            icon_path = '%s.%s' % (ext, icon_ext)
            if exists(join(icons_dir, icon_path)):
                return icon_path
    icon_path = '%s.png' % mimetype.major()
    if exists(join(icons_dir, icon_path)):
        return icon_path
    return 'unknown.png'


def split(name):
    """ split a mime type in a (major / minor) 2-uple """
    try:
        major, minor = name.split('/', 1)
    except:
        raise MimeTypeException('Malformed MIME type (%s)' % name)
    return major, minor
