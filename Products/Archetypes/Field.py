from __future__ import nested_scopes
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_base
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore.utils import getToolByName
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from Widget import *
from utils import capitalize, DisplayList
from debug import log, log_exc
from ZPublisher.HTTPRequest import FileUpload
from BaseUnit import BaseUnit
from types import StringType, UnicodeType
from Storage import AttributeStorage, MetadataStorage, ObjectManagedStorage, \
     ReadOnlyStorage
from DateTime import DateTime
from Layer import DefaultLayerContainer
from interfaces.field import IField, IObjectField
from interfaces.layer import ILayerContainer, ILayerRuntime, ILayer
from interfaces.storage import IStorage
from interfaces.base import IBaseUnit
from exceptions import ObjectFieldException, TextFieldException, FileFieldException
from Products.validation import validation
from config import TOOL_NAME, USE_NEW_BASEUNIT
from OFS.content_types import guess_content_type
from OFS.Image import File

#For Backcompat and re-export
from Schema import FieldList, MetadataFieldList

STRING_TYPES = [StringType, UnicodeType]

class Field(DefaultLayerContainer):
    __implements__ = (IField, ILayerContainer)

    security  = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'required' : 0,
        'default' : None,
        'default_method' : None,
        'vocabulary' : (),
        'enforceVocabulary' : 0,
        'multiValued' : 0,
        'searchable' : 0,
        'isMetadata' : 0,

        'accessor' : None,
        'mutator' : None,
        'mode' : 'rw',

        'read_permission' : CMFCorePermissions.View,
        'write_permission' : CMFCorePermissions.ModifyPortalContent,

        'storage' : AttributeStorage(),

        'generateMode' : 'veVc',
        'force' : '',
        'type' : None,
        'widget': StringWidget,
        'validators' : (),
        'index' : None, # "KeywordIndex" "<type>|schema"
        'schemata' : 'default',
        }

    def __init__(self, name, **kwargs):
        DefaultLayerContainer.__init__(self)

        self.name = name

        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)

        self._widgetLayer()
        self._validationLayer()

        self.registerLayer('storage', self.storage)

    def copy(self):
        return self.__class__(**self.__dict__)

    def __repr__(self):
        return "<Field %s(%s:%s)>" %(self.name, self.type, self.mode)

    def _widgetLayer(self):
        if hasattr(self, 'widget') and type(self.widget) == ClassType:
            self.widget = self.widget()

    def _validationLayer(self):
        # resolve that each validator is in the service
        # we could replace strings with class refs and keep
        # things impl the ivalidator in the list
        # XXX this is not compat with aq_ things like scripts with
        # __call__
        if type(self.validators) not in [type(()), type([])]:
            self.validators = (self.validators,)

        for v in self.validators:
            if not validation.validatorFor(v):
                log("WARNING: no validator %s for %s" % (v,
                self.name))

    def validate(self, value):
        for v in self.validators:
            res = validation.validate(v, value)
            if res != 1:
                return res
            return None

    def Vocabulary(self, content_instance=None):
        value = self.vocabulary
        if not isinstance(value, DisplayList):
            if content_instance is not None and type(value) in STRING_TYPES:
                method = getattr(content_instance, value, None)
                if method and callable(method):
                    value = method()

            # Post process value into a DisplayList, templates will use
            # this interface
            sample = value[:1]
            if isinstance(sample, DisplayList):
                #Do nothing, the bomb is already set up
                pass
            elif type(sample) in [TupleType, ListType]:
                #Assume we have ( (value, display), ...)
                #and if not ('', '', '', ...)
                if len(sample) != 2:
                    value = zip(value, value)
                value = DisplayList(value)
            elif len(sample) and type(sample[0]) == type(''):
                value = DisplayList(zip(value, value))
            else:
                log("Unhandled type in Vocab")
                log(value)

        return value

    def checkPermission(self, mode, instance):
        if mode in ('w', 'write', 'edit', 'set'):
            perm = self.write_permission
        elif mode in ('r', 'read', 'view', 'get'):
            perm = self.read_permission
        else:
            return None
        return getSecurityManager().checkPermission( perm, instance )

    security.declarePublic('checkExternalEditor')
    def checkExternalEditor(self, instance):
        """ Checks if the user may edit this field and if
        external editor is enabled on this instance """
        pp = getToolByName(instance, 'portal_properties')
        sp = getattr(pp, 'site_properties', None)
        if sp is not None:
            if getattr(sp, 'ext_editor', None) and self.checkPermission(mode='edit', instance=instance):
                return 1
        return None

    security.declarePublic('getStorageName')
    def getStorageName(self):
        return self.storage.getName()

    security.declarePublic('getWidgetName')
    def getWidgetName(self):
        return self.widget.getName()

    security.declarePublic('getName')
    def getName(self):
        return self.name

    security.declarePublic('getDefault')
    def getDefault(self):
        return self.default

    security.declarePrivate('getAccessor')
    def getAccessor(self, instance):
        return getattr(instance, self.accessor, None)

    security.declarePublic('getMutator')
    def getMutator(self, instance):
        return getattr(instance, self.mutator, None)

class ObjectField(Field):
    """Base Class for Field objects that fundamentaly deal with raw
    data. This layer implements the interface to IStorage and other
    Field Types should subclass this to delegate through the storage
    layer.
    """
    __implements__ = (IObjectField, ILayerContainer)

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'default_content_type' : 'application/octet',
        })

    def get(self, instance, **kwargs):
        try:
            kwargs['field'] = self
            return self.storage.get(self.name, instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', 0):
                self.set(instance,self.default,_initializing_=1,**kwargs)
            return self.default

    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        # Remove acquisition wrappers
        value = aq_base(value)
        self.storage.set(self.name, instance, value, **kwargs)

    def unset(self, instance, **kwargs):
        kwargs['field'] = self
        self.storage.unset(self.name, instance, **kwargs)

    def setStorage(self, instance, storage):
        if not IStorage.isImplementedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        value = self.get(instance)
        self.unset(instance)
        self.storage = storage
        if hasattr(self.storage, 'initializeInstance'):
            self.storage.initializeInstance(instance)
        self.set(instance, value)

    def getStorage(self):
        return self.storage

class StringField(ObjectField):
    """A string field"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'string',
        'default': '',
        'default_content_type' : 'text/plain',
        })

class MetadataField(ObjectField):
    """Metadata fields have special storage and explictly no markup as
    requirements.
    """
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'metadata',
        'isMetadata' : 1,
        'generateMode' : 'mVc',
        'mode' : 'rw',
        'storage' : MetadataStorage(),
        })


class FileField(StringField):
    """Something that may be a file, but is not an image and doesn't
    want text format conversion"""

    __implements__ = ObjectField.__implements__

    _properties = StringField._properties.copy()
    _properties.update({
        'type' : 'file',
        'default' : '',
        'primary' : 0,
        })

    def _process_input(self, value, default=None,
                       mime_type=None, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if type(value) in STRING_TYPES:
            if mime_type is None:
                mime_type, enc = guess_content_type('', value, mime_type)
            if not value:
                return default, mime_type
            return value, mime_type
        elif ((isinstance(value, FileUpload) and value.filename != '') or
              (isinstance(value, FileType) and value.name != '')):
            f_name = ''
            if isinstance(value, FileUpload):
                f_name = value.filename
            if isinstance(value, FileType):
                f_name = value.name
            value = value.read()
            if mime_type is None:
                mime_type, enc = guess_content_type(f_name, value, mime_type)
            size = len(value)
            if size == 0:
                # This new file has no length, so we keep
                # the orig
                return default, mime_type
            return value, mime_type
        raise FileFieldException('Value is not File or String')

    def getContentType(self, instance):
        if hasattr(aq_base(instance), '_FileField_types'):
            return instance._FileField_types.get(self.getName(), None)
        return None

    def set(self, instance, value, **kwargs):
        if not kwargs.has_key('mime_type'):
            kwargs['mime_type'] = None

        value, mime_type = self._process_input(value,
                                               default=self.default, \
                                               **kwargs)
        kwargs['mime_type'] = mime_type

        # FIXME: ugly hack
        try:
            types_d = instance._FileField_types
        except AttributeError:
            types_d = {}
            instance._FileField_types = types_d
        types_d[self.name] = mime_type
        value = File(self.name, '', value, mime_type)
        ObjectField.set(self, instance, value, **kwargs)

class TextField(ObjectField):
    """Base Class for Field objects that rely on some type of
    transformation"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'text',
        'default' : '',
        'default_content_type' : 'text/plain',
        'default_output_type'  : 'text/plain',
        'allowable_content_types' : ('text/plain',),
        'primary' : 0,
        })

    def defaultView(self):
        return self.default_output_type

    def _process_input(self, value, default=None, \
                       mime_type=None, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if type(value) in STRING_TYPES:
            if mime_type is None:
                mime_type, enc = guess_content_type('', str(value), mime_type)
            if not value:
                return default, mime_type
            return value, mime_type
        else:
            if ((isinstance(value, FileUpload) and value.filename != '') or
                (isinstance(value, FileType) and value.name != '')):
                #OK, its a file, is it empty?
                f_name = ''
                if isinstance(value, FileUpload):
                    f_name = value.filename
                if isinstance(value, FileType):
                    f_name = value.name
                value = value.read()
                if mime_type is None:
                    mime_type, enc = guess_content_type(f_name, value, mime_type)
                size = len(value)
                if size == 0:
                    # This new file has no length, so we keep
                    # the orig
                    return default, mime_type
                return value, mime_type

            elif IBaseUnit.isImplementedBy(value):
                if mime_type is None:
                    mime_type, enc = guess_content_type('', str(value), mime_type)
                return value, getattr(aq_base(value), 'mimetype', mime_type)

        raise TextFieldException('Value is not File, String or BaseUnit on %s: %r' % (self.name, type(value)))

    def getContentType(self, instance):
        value = ''
        accessor = self.getAccessor(instance)
        if accessor is not None:
            value = accessor()
        mime_type = getattr(aq_base(value), 'mimetype', None)
        if mime_type is None:
            mime_type, enc = guess_content_type('', str(value), None)
        return mime_type

    def set(self, instance, value, **kwargs):
        if not kwargs.has_key('mime_type'):
            kwargs['mime_type'] = None

        value, mime_type = self._process_input(value,
                                               default=self.default, \
                                               **kwargs)
        kwargs['mime_type'] = mime_type

        if IBaseUnit.isImplementedBy(value):
            bu = value
        else:
            bu = BaseUnit(self.name, value, mime_type=mime_type)

        ObjectField.set(self, instance, bu, **kwargs)

        #Invoke the default Transforms, hey, its policy
        #Note that we stash the product of transforms on
        #bu.transforms and BU deals with that
        #tt = getToolByName(self, "transformation_tool")
        #tt.runChains(MUTATION,
        #             bu.getRaw(),
        #             bu.transforms)


class DateTimeField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    def set(self, instance, value, **kwargs):
        if not value:
            value = None
        elif not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                value = None

        ObjectField.set(self, instance, value, **kwargs)

class LinesField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'lines',
        'default' : [],
        'widget' : LinesWidget,
        })

    def set(self, instance, value, **kwargs):
        if type(value) == type(''):
            value =  value.split('\n')
        value = [v.strip() for v in value if v.strip()]
        value = filter(None, value)
        ObjectField.set(self, instance, value, **kwargs)

class IntegerField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer',
        'size' : '10',
        'default' : 0
        })

    def set(self, instance, value, **kwargs):
        try:
            value = int(value)
        except TypeError:
            value = self.default

        ObjectField.set(self, instance, value, **kwargs)

class FloatField(ObjectField):
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'float'
        })

    def set(self, instance, value, **kwargs):
        try:
            value = float(value)
        except TypeError:
            value = None

        ObjectField.set(self, instance, value, **kwargs)

class FixedPointField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'fixedpoint',
        'precision' : 2,
        'default' : '0.0',
        'widget' : DecimalWidget,
        'validators' : ('isDecimal'),
        })

    def _to_tuple(self, value):
        value = value.split('.') # FIXME: i18n?
        if len(value) < 2:
            value = (int(value[0]), 0)
        else:
            fra = value[1][:self.precision]
            fra += '0' * (self.precision - len(fra))
            value = (int(value[0]), int(fra))
        return value

    def set(self, instance, value, **kwargs):
        value = self._to_tuple(value)
        ObjectField.set(self, instance, value, **kwargs)

    def get(self, instance, **kwargs):
        template = '%%d.%%0%dd' % self.precision
        value = ObjectField.get(self, instance, **kwargs)
        __traceback_info__ = (template, value)
        if value is None: return self.default
        if type(value) in [StringType]: value = self._to_tuple(value)
        return template % value

class ReferenceField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'reference',
        'default': None,
        'widget' : ReferenceWidget,
        'allowed_types' : (),
        'addable': 0,
        'destination': None,
        })

    def Vocabulary(self, content_instance=None):
        #If we have a method providing the list of types go with it,
        #it can always pull allowed_types if it needs to (not that we
        #pass the field name)
        value = ObjectField.Vocabulary(self, content_instance)
        if value:
            return value
        if self.allowed_types:
            catalog = getToolByName(content_instance, 'portal_catalog')
            value = [(obj.UID, str(obj.Title).strip() or \
                      str(obj.getId).strip()) \
                     for obj in catalog(Type=self.allowed_types)]
        else:
            archetype_tool = getToolByName(content_instance, TOOL_NAME)
            value = [(obj.UID, str(obj.Title).strip() or \
                      str(obj.getId).strip()) \
                     for obj in archetype_tool.Content()]
        if not self.required:
            value.insert(0, ('', '<no reference>'))
        return DisplayList(value)

class ComputedField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'computed',
        'expression': None,
        'widget' : ComputedWidget,
        'mode' : 'r',
        'storage': ReadOnlyStorage(),
        })

    def set(self, *ignored, **kwargs):
        pass

    def get(self, instance, **kwargs):
        return eval(self.expression, {'context': instance})

class BooleanField(ObjectField):
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'widget' : BooleanWidget,
        })

    def set(self, instance, value, **kwargs):

        if not value or value == '0':
            value = None ## False
        else:
            value = 1

        ObjectField.set(self, instance, value, **kwargs)

class CMFObjectField(ObjectField):
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'portal_type': 'File',
        'default': None,
        'default_mime_type': 'application/octet-stream',
        'widget' : FileWidget(),
        'storage': ObjectManagedStorage(),
        'workflowable': 1,
        })

    def _process_input(self, value, default=None, **kwargs):
        __traceback_info__ = (value, type(value))
        if type(value) != StringType:
            if ((isinstance(value, FileUpload) and value.filename != '') or \
                (isinstance(value, FileType) and value.name != '')):
                #OK, its a file, is it empty?
                value.seek(-1, 2)
                size = value.tell()
                value.seek(0)
                if size == 0:
                    # This new file has no length, so we keep
                    # the orig
                    return default
                return value
            if value is None:
                return default
        else:
            if value == '':
                return default
            return value

        raise ObjectFieldException('Value is not File or String')

    def get(self, instance, **kwargs):
        try:
            return self.storage.get(self.name, instance, **kwargs)
        except AttributeError:
            # object doesnt exists
            tt = getToolByName(instance, 'portal_types', None)
            if tt is None:
                msg = "Coudln't get portal_types tool from this context"
                raise AttributeError(msg)
            type_name = self.portal_type
            info = tt.getTypeInfo(type_name)
            if info is None:
                raise ValueError('No such content type: %s' % type_name)
            if not hasattr(aq_base(info), 'constructInstance'):
                raise ValueError('Cannot construct content type: %s' % \
                                 type_name)
            return info.constructInstance(instance, self.name, **kwargs)

    def set(self, instance, value, **kwargs):
        obj = self.get(instance, **kwargs)
        value = self._process_input(value, default=self.default, \
                                    **kwargs)
        if value is None or value == '':
            # do nothing
            return

        obj.edit(file=value)
        # The object should be already stored, so we dont 'set' it,
        # but just change instead.
        # ObjectField.set(self, instance, obj, **kwargs)

InitializeClass(Field)

# new image field implementation, derived from CMFPhoto by Magnus Heino

from cgi import escape
from cStringIO import StringIO
import sys
from zLOG import LOG, ERROR
from BTrees.OOBTree import OOBTree
from ExtensionClass import Base
from Acquisition import Implicit, aq_parent
from OFS.Traversable import Traversable
from OFS.Image import Image as BaseImage

try: 
    import PIL.Image
    isPilAvailable = 1
except ImportError: 
    isPilAvailable = 0

class DynVariantWrapper(Base):
    """
        Provide a transparent wrapper from image to dynvariant
        call it with url ${image_url}/variant/${variant}
    """

    def __of__(self, parent):
        return parent.Variants()

class DynVariant(Implicit, Traversable):
    """
        Provide access to the variants.
    """

    def __init__(self):
        pass

    def __getitem__(self, name):
        if self.checkForVariant(name):
            return self.getPhoto(name).__of__(aq_parent(self))
        else:
            return aq_parent(self)

class ScalableImage(BaseImage):
    """
        A scalable image class.
    """

    __implements__ = BaseImage.__implements__

    meta_type = 'Scalable Image'

    isBinary = lambda self: 1

    def __init__(self, id, title='', file='', displays={}):
        BaseImage.__init__(self, id, title, file)
        self._photos = OOBTree()
        self.displays = displays

    security = ClassSecurityInfo()

    # make image variants accesable via url
    variant=DynVariantWrapper()

    security.declareProtected(CMFCorePermissions.View, 'Variants')
    def Variants(self):
        # Returns a variants wrapper instance
        return DynVariant().__of__(self) 

    security.declareProtected(CMFCorePermissions.View, 'getPhoto')
    def getPhoto(self,size):
        '''returns the Photo of the specified size'''
        return self._photos[size]

    security.declareProtected(CMFCorePermissions.View, 'getDisplays')
    def getDisplays(self):
        result = []
        for name, size in self.displays.items():
            result.append({'name':name, 'label':'%s (%dx%d)' % (
                name, size[0], size[1]),'size':size}
                )

        #sort ascending by size
        result.sort(lambda d1,d2: cmp(
            d1['size'][0]*d1['size'][0],
            d2['size'][1]*d2['size'][1])
            )
        return result

    security.declarePrivate('checkForVariant')
    def checkForVariant(self, size):
	"""Create variant if not there."""
        if size in self.displays.keys():
	    # Create resized copy, if it doesnt already exist
            if not self._photos.has_key(size):
                self._photos[size] = BaseImage(
                    size, size, self._resize(self.displays.get(size, (0,0)))
                    )
            # a copy with a content type other than image/* exists, this
            # probably means that the last resize process failed. retry
            elif not self._photos[size].getContentType().startswith('image'):
                self._photos[size] = BaseImage(
                    size, size, self._resize(self.displays.get(size, (0,0)))
                    )
            return 1
        else: 
            return 0

    security.declareProtected(CMFCorePermissions.View, 'index_html')
    def index_html(self, REQUEST, RESPONSE, size=None):
        """Return the image data."""
        if self.checkForVariant(size):
            return self.getPhoto(size).index_html(REQUEST, RESPONSE)
        return BaseImage.index_html(self, REQUEST, RESPONSE)

    security.declareProtected(CMFCorePermissions.View, 'tag')
    def tag(self, height=None, width=None, alt=None,
            scale=0, xscale=0, yscale=0, css_class=None, 
            title=None, size='original', **args):
        """ Return an HTML img tag (See OFS.Image)"""

        # Default values
        w=self.width
        h=self.height

        if height is None or width is None:

            if size in self.displays.keys():
                if not self._photos.has_key(size):
                    # This resized image isn't created yet.
                    # Calculate a size for it
                    x,y = self.displays.get(size)
                    try:
                        if self.width > self.height:
                            w=x
                            h=int(round(1.0/(float(self.width)/w/self.height)))
                        else:
                            h=y
                            w=int(round(1.0/(float(self.height)/x/self.width)))
                    except ValueError:
                        # OFS.Image only knows about png, jpeg and gif.
                        # Other images like bmp will not have height and
                        # width set, and will generate a ValueError here.
                        # Everything will work, but the image-tag will render 
                        # with height and width attributes.
                        w=None
                        h=None
                else:
                    # The resized image exist, get it's size
                    photo = self._photos.get(size)
                    w=photo.width
                    h=photo.height

        if height is None: height=h
        if width is None:  width=w

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width =  str(int(round(int(width) * xdelta)))
        if ydelta and height:
            height = str(int(round(int(height) * ydelta)))

        result='<img src="%s/variant/%s"' % (self.absolute_url(), escape(size))

        if alt is None:
            alt=getattr(self, 'title', '')
        result = '%s alt="%s"' % (result, escape(alt, 1))

        if title is None:
            title=getattr(self, 'title', '')
        result = '%s title="%s"' % (result, escape(title, 1))

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if not 'border' in [ x.lower() for x in args.keys()]:
            result = '%s border="0"' % result

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in args.keys():
            value = args.get(key)
            result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

    security.declarePrivate('update_data')
    def update_data(self, data, content_type=None, size=None):
        """
            Update/upload image -> remove all copies
        """
        BaseImage.update_data(self, data, content_type, size)
        self._photos = OOBTree()
        
    def _resize(self, size, quality=100):
        """Resize and resample photo."""
        image = StringIO()

        width, height = size

        try:
            if isPilAvailable:
                img = PIL.Image.open(StringIO(str(self.data)))
                fmt = img.format
                # Resize photo
                img.thumbnail((width, height))
                # Store copy in image buffer
                img.save(image, fmt, quality=quality)
            else:
                if sys.platform == 'win32':
                    from win32pipe import popen2
                    imgin, imgout = popen2('convert -quality %s -geometry %sx%s - -'
                                           % (quality, width, height), 'b')
                else:
                    from popen2 import Popen3
                    convert=Popen3('convert -quality %s -geometry %sx%s - -'
                                           % (quality, width, height))
                    imgout=convert.fromchild
                    imgin=convert.tochild

                imgin.write(str(self.data))
                imgin.close()
                image.write(imgout.read())
                imgout.close()

                #Wait for process to close if unix. Should check returnvalue for wait
                if sys.platform !='win32':
                    convert.wait()

                image.seek(0)
                
        except Exception, e:
            LOG('Archetypes.ScallableField', ERROR, 'Error while resizing image', e)
                
        return image

InitializeClass(ScalableImage)

class ImageField(ObjectField):
    """
        An image field class.
    """

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'default_content_type' : 'image/gif',
        'allowable_content_types' : ('image/gif','image/jpeg'),
        'displays': {
            'thumbnail': (128,128),
            'xsmall': (200,200),
            'small': (320,320),
            'medium': (480,480),
            'large': (768,768),
            'xlarge': (1024,1024)
            },
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        })

    default_view = "view"

    def set(self, instance, value, **kw):
        if isinstance(value, StringType):
            value = StringIO(value)
        image = ScalableImage(self.name, file=value, displays=self.displays)
        ObjectField.set(self, instance, image, **kw)

InitializeClass(ImageField)

__all__ = ('Field', 'ObjectField', 'StringField', 'MetadataField', \
           'FileField', 'TextField', 'DateTimeField', 'LinesField', \
           'IntegerField', 'FloatField', 'FixedPointField', \
           'ReferenceField', 'ComputedField', 'BooleanField', \
           'CMFObjectField', 'ImageField', \
           'FieldList', 'MetadataFieldList', # Those two should go
                                             # away after 1.0
           )

