from __future__ import nested_scopes
from copy import deepcopy
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_base, aq_parent, aq_inner
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore.utils import getToolByName
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from Widget import *
from utils import capitalize, DisplayList, className
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
from exceptions import ObjectFieldException, TextFieldException, \
     FileFieldException
from config import TOOL_NAME, USE_NEW_BASEUNIT
from OFS.content_types import guess_content_type
from OFS.Image import File
from ZODB.PersistentMapping import PersistentMapping
from ComputedAttribute import ComputedAttribute
from Products.PortalTransforms.interfaces import idatastream

try:
    from validation import validation
except ImportError:
    from Products.validation import validation

STRING_TYPES = [StringType, UnicodeType]
"""Mime-types currently supported"""

__docformat__ = 'reStructuredText'

def getLanguage(instance, lang):
    try:
        return instance.getContentLanguage(lang)
    except AttributeError:
        # this may occurs during object construction
        # FIXME : in that case, we would like to get a default language from portal_properties
        return 'en'

def encode(value, instance, **kwargs):
    """ensure value is an encoded string"""
    if type(value) is type(u''):
        encoding = kwargs.get('encoding')
        if encoding is None:
            site_props = instance.portal_properties.site_properties
            encoding = site_props.getProperty('default_charset')
        value = value.encode(encoding)
    return value

def decode(value, instance, **kwargs):
    """ensure value is an unicode string"""
    if type(value) is type(''):
        encoding = kwargs.get('encoding')
        if encoding is None:
            site_props = instance.portal_properties.site_properties
            encoding = site_props.getProperty('default_charset')
        value = unicode(value, encoding)
    return value


class Field(DefaultLayerContainer):
    """
    Extend `DefaultLayerContainer`.
    Implements `IField` and `ILayerContainer` interfaces.
    Class security = public with default access = allow.
    Class attribute _properties is a dictionary containing all of a
    field's property values.
    """

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
        'edit_accessor' : None,
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
        'index' : None, # "KeywordIndex" or "<index_type>:schema"
        'schemata' : 'default',
        }

    def __init__(self, name, **kwargs):
        """
        Assign name to __name__. Add properties and passed-in
        keyword args to __dict__. Validate assigned validator(s).
        """
        DefaultLayerContainer.__init__(self)

        self.__name__ = name

        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)

        self._widgetLayer()
        self._validationLayer()

        self.registerLayer('storage', self.storage)

    def copy(self):
        """
        Return a copy of field instance, consisting of field name and
        properties dictionary.
        """
        properties = deepcopy(self.__dict__)
        return self.__class__(self.getName(), **properties)

    def __repr__(self):
        """
        Return a string representation consisting of name, type and permissions.
        """
        return "<Field %s(%s:%s)>" %(self.getName(), self.type, self.mode)

    def _widgetLayer(self):
        """
        instantiate the widget if a class was given
        """
        if hasattr(self, 'widget') and type(self.widget) == ClassType:
            self.widget = self.widget()

    def _validationLayer(self):
        """
        Resolve that each validator is in the service. If validator is
        not, log a warning.

        We could replace strings with class refs and keep things impl
        the ivalidator in the list.

        Note: XXX this is not compat with aq_ things like scripts with __call__
        """
        if type(self.validators) not in [type(()), type([])]:
            self.validators = (self.validators,)

        for v in self.validators:
            if not validation.validatorFor(v):
                log("WARNING: no validator %s for %s" % (v,
                self.getName()))

    def validate(self, value, **kwargs):
        """
        Validate passed-in value using all field validators.
        Return None if all validations pass; otherwise, return failed
        result returned by validator
        """
        for v in self.validators:
            res = validation.validate(v, value, **kwargs)
            if res != 1:
                return res
            return None

    def Vocabulary(self, content_instance=None):
        """
        COMMENT TODO
        """

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
        """
        Check whether the security context allows the given permission on
        the given object.

        Arguments:

        permission -- A permission name
        instance -- The object being accessed according to the permission
        """
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
        """Return the storage name that is configured for this field as a string"""
        return self.storage.getName()

    security.declarePublic('getWidgetName')
    def getWidgetName(self):
        """Return the widget name that is configured for this field as a string"""
        return self.widget.getName()

    security.declarePublic('getName')
    def getName(self):
        """Return the name of this field as a string"""
        return self.__name__

    security.declarePublic('getType')
    def getType(self):
        """Return the type of this field as a string"""
        return className(self)

    security.declarePublic('getDefault')
    def getDefault(self):
        """Return the default value to be used for initializing this field"""
        return self.default

    security.declarePrivate('getAccessor')
    def getAccessor(self, instance):
        """Return the accessor method for getting data out of this field"""
        if self.accessor:
            return getattr(instance, self.accessor, None)
        return None

    security.declarePrivate('getEditAccessor')
    def getEditAccessor(self, instance):
        """Return the accessor method for getting raw data out of this
        field e.g.: for editing
        """
        if self.edit_accessor:
            return getattr(instance, self.edit_accessor, None)
        return None

    security.declarePublic('getMutator')
    def getMutator(self, instance):
        """Return the mutator method used for changing the value
        of this field"""
        if self.mutator:
            return getattr(instance, self.mutator, None)
        return None

    def hasI18NContent(self):
        """Return true it the field has I18N content. Currently not
        implemented."""
        return 0

    def toString(self):
        """Utility method for converting a Field to a string for the purpose of
        comparing fields.  This comparison is used for determining whether a
        schema has changed in the auto update function.  Right now it's pretty
        crude."""
        # XXX fixme
        s = '%s: {' % self.__class__.__name__
        sorted_keys = self._properties.keys()
        sorted_keys.sort()
        for k in sorted_keys:
            s = s + '%s:%s,' % (k, self._properties[k])
        s = s + '}'
        return s


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
            return self.storage.get(self.getName(), instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', 0):
                self.set(instance, self.default,_initializing_=1,**kwargs)
            return self.default

    def getRaw(self, instance, **kwargs):
        if self.accessor is not None:
            accessor = self.getAccessor(instance)
        else:
            # self.accessor is None for fields wrapped by an I18NMixIn
            accessor = None
        if accessor is None:
            return self.get(instance, **kwargs)
        return accessor(**kwargs)

    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        # Remove acquisition wrappers
        value = aq_base(value)
        self.storage.set(self.getName(), instance, value, **kwargs)

    def unset(self, instance, **kwargs):
        kwargs['field'] = self
        self.storage.unset(self.getName(), instance, **kwargs)

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
    """A field that stores strings"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'string',
        'default': '',
        'default_content_type' : 'text/plain',
        })

    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        return encode(value, instance, **kwargs)

    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        # Remove acquisition wrappers
        value = decode(aq_base(value), instance, **kwargs)
        self.storage.set(self.getName(), instance, value, **kwargs)

class FileField(StringField):
    """Something that may be a file, but is not an image and doesn't
    want text format conversion"""

    __implements__ = ObjectField.__implements__

    _properties = StringField._properties.copy()
    _properties.update({
        'type' : 'file',
        'default' : '',
        'primary' : 0,
        'widget' : FileWidget,
        })

    def _process_input(self, value, default=None,
                       mimetype=None, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if type(value) in STRING_TYPES:
            if mimetype is None:
                mimetype, enc = guess_content_type('', value, mimetype)
            if not value:
                return default, mimetype
            return value, mimetype
        elif ((isinstance(value, FileUpload) and value.filename != '') or
              (isinstance(value, FileType) and value.name != '')):
            f_name = ''
            if isinstance(value, FileUpload):
                f_name = value.filename
            if isinstance(value, FileType):
                f_name = value.name
            value = value.read()
            if mimetype is None:
                mimetype, enc = guess_content_type(f_name, value, mimetype)
            size = len(value)
            if size == 0:
                # This new file has no length, so we keep
                # the orig
                return default, mimetype
            return value, mimetype
        raise FileFieldException('Value is not File or String')

    def getContentType(self, instance):
        """Return the type of file of this object if known; otherwise,
        return None."""
        if hasattr(aq_base(instance), '_FileField_types'):
            return instance._FileField_types.get(self.getName(), None)
        return None

    def set(self, instance, value, **kwargs):
        """
        Assign input value to object. If mimetype is not specified,
        pass to processing method without one and add mimetype returned
        to kwargs. Assign kwargs to instance.
        """
        if not kwargs.has_key('mimetype'):
            kwargs['mimetype'] = None

        value, mimetype = self._process_input(value,
                                               default=self.default,
                                               **kwargs)
        kwargs['mimetype'] = mimetype

        # FIXME: ugly hack
        try:
            types_d = instance._FileField_types
        except AttributeError:
            types_d = {}
            instance._FileField_types = types_d
        types_d[self.getName()] = mimetype
        value = File(self.getName(), '', value, mimetype)
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

    def _process_input(self, value, default=None, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if ((isinstance(value, FileUpload) and value.filename != '') or
            (isinstance(value, FileType) and value.name != '')):
            #OK, its a file, is it empty?
            if not value.read(1):
                # This new file has no length, so we keep
                # the orig
                return default
            value.seek(0)
            return value

        if IBaseUnit.isImplementedBy(value):
            return value

        if type(value) in STRING_TYPES:
            return value

        raise TextFieldException('Value is not File, String or BaseUnit on %s: %r' % (self.getName(), type(value)))

    def getContentType(self, instance):
        """Return the mime type of object if known or can be guessed;
        otherwise, return None."""
        value = ''
        accessor = self.getAccessor(instance)
        if accessor is not None:
            value = accessor(raw=1)
        mimetype = getattr(aq_base(value), 'mimetype', None)
        if mimetype is None:
            mimetype, enc = guess_content_type('', str(value), None)
        else:
            # mimetype may be an imimetype object
            mimetype = str(mimetype)
        return mimetype


    def getRaw(self, instance, raw=0, **kwargs):
        """
        if raw, return the base unit object, else return encoded raw data
        """
        value = self.get(instance, raw=1, **kwargs)
        if raw or not IBaseUnit.isImplementedBy(value):
            return value
        try:
            return value.getRaw(encoding=kwargs.get('encoding'), instance=instance)
        except TypeError:
            # FIXME: backward compat, getRaw doesn't take encoding argument on old base units
            value.getRaw()

    def get(self, instance, mimetype=None, raw=0, **kwargs):
        """
        if raw, return the base unit object,
        else return value of object transformed into requested mime type.

        If no requested type, then return value in default type. If raw
        format is specified, try to transform data into the default output type
        or to plain text.
        If we are unable to transform data, return an empty string.
        """
        try:
            kwargs['field'] = self
            value = self.storage.get(self.getName(), instance, **kwargs)
            if not IBaseUnit.isImplementedBy(value):
                return encode(value, instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', 0):
                self.set(instance, self.default, _initializing_=1, **kwargs)
            return self.default

        if raw:
            return value

        if mimetype is None:
            mimetype =  self.default_output_type or 'text/plain'

        if not hasattr(value, 'transform'): # oldBaseUnits have no transform
            return str(value)
        data = value.transform(instance, mimetype)
        if not data and mimetype != 'text/plain':
            data = value.transform(instance, 'text/plain')
        return data or ''


    def set(self, instance, value, **kwargs):
        """
        Assign input value to object. If mimetype is not specified,
        pass to processing method without one and add mimetype returned
        to kwargs. Assign kwargs to instance.
        """
        value = self._process_input(value, default=self.default, **kwargs)
        encoding = kwargs.get('encoding')
        if type(value) is type(u'') and encoding is None:
            encoding = 'UTF-8'

        if not IBaseUnit.isImplementedBy(value):
            value = BaseUnit(self.getName(), value, instance=instance,
                             encoding=encoding,
                             mimetype=kwargs.get('mimetype'))

        ObjectField.set(self, instance, value, **kwargs)

    def setStorage(self, instance, storage):
        if not IStorage.isImplementedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        value = self.get(instance, raw=1)
        self.unset(instance)
        self.storage = storage
        if hasattr(self.storage, 'initializeInstance'):
            self.storage.initializeInstance(instance)
        self.set(instance, value)


class DateTimeField(ObjectField):
    """A field that stores dates and times"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    def set(self, instance, value, **kwargs):
        """
        Check if value is an actual date/time value. If not, attempt
        to convert it to one; otherwise, set to None. Assign all
        properties passed as kwargs to object.
        """
        if not value:
            value = None
        elif not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                value = None

        ObjectField.set(self, instance, value, **kwargs)

class LinesField(ObjectField):
    """For creating lines objects"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'lines',
        'default' : [],
        'widget' : LinesWidget,
        })

    def set(self, instance, value, **kwargs):
        """
        If passed-in value is a string, split at line breaks and
        remove leading and trailing white space before storing in object
        with rest of properties.
        """
        __traceback_info__ = value, type(value)
        if type(value) in STRING_TYPES:
            value =  value.split('\n')
        value = [decode(v.strip(), instance, **kwargs) for v in value if v.strip()]
        value = filter(None, value)
        ObjectField.set(self, instance, value, **kwargs)

    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        return [encode(v, instance, **kwargs) for v in value]

class IntegerField(ObjectField):
    """A field that stores an integer"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer',
        'size' : '10',
        'default' : 0
        })

    def set(self, instance, value, **kwargs):
        if value=='':
            value=None
        elif value is not None:
            # should really blow if value is not valid
            __traceback_info__ = (self.getName(), instance, value, kwargs)
            value = int(value)

        ObjectField.set(self, instance, value, **kwargs)

class FloatField(ObjectField):
    """A field that stores floats"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'float',
        'default': '0.0'
        })

    def set(self, instance, value, **kwargs):
        """Convert passed-in value to a float. If failure, set value to
        None."""
        if value=='':
            value=None
        elif value is not None:
            # should really blow if value is not valid
            __traceback_info__ = (self.getName(), instance, value, kwargs)
            value = float(value)

        ObjectField.set(self, instance, value, **kwargs)

class FixedPointField(ObjectField):
    """A field for storing numerical data with fixed points"""
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
        """ COMMENT TO-DO """
        if not value:
            value = self.default # Does this sounds right?
        value = value.split('.')
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
    """A field for containing a reference"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'reference',
        'default': None,
        'widget' : ReferenceWidget,
        'allowed_types' : (),
        'addable': 0,
        'destination': None,
        'relationship':None
        })

    def containsValueAsString(self,value,attrval):
        """
        checks wether the attribute contains a value
           if the field is a scalar -> comparison
           if it is multiValued     -> check for 'in'
        """
        if self.multiValued:
            return str(value) in [str(a) for a in attrval]
        else:
            return str(value) == str(attrval)

    def set(self, instance, value, **kwargs):
        """ Add one or more passed in references to the object.
        Before setting the value the reference gets also be established
        in the reference tool
        """

        if not value:
            value=None
        __traceback_info__ = (instance, self.getName(), value)

        #establish the relation through the ReferenceEngine
        tool=getToolByName(instance,TOOL_NAME)
        refname=self.relationship

        #XXX: thats too cheap, but I need the proof of concept before going on
        instance.deleteReferences(refname)
        newValue = []
        if self.multiValued:
            if type(value) in (type(()),type([])):
                for uid in value:
                    if uid:
                        target=tool.lookupObject(uid=uid)
                        if target is None:
                            raise ValueError, "Invalid reference %s" % uid
                        instance.addReference(target,refname)
                        newValue.append(uid)
        else:
            if value:
                target=tool.lookupObject(uid=value)
                if target is None:
                    raise ValueError, "Invalid reference %s" % value
                instance.addReference(target,refname)
                newValue = value

        #and now do the normal assignment
        ObjectField.set(self, instance, newValue, **kwargs)

    def Vocabulary(self, content_instance=None):
        #If we have a method providing the list of types go with it,
        #it can always pull allowed_types if it needs to (not that we
        #pass the field name)
        value = ObjectField.Vocabulary(self, content_instance)
        if value:
            return value
        results = []
        if self.allowed_types:
            catalog = getToolByName(content_instance, 'portal_catalog')
            results = catalog(Type=self.allowed_types)
        else:
            archetype_tool = getToolByName(content_instance, TOOL_NAME)
            results = archetype_tool.Content()
        results = [(r, r.getObject()) for r in results]
        value = [(r.UID, obj and (str(obj.Title().strip()) or \
                                  str(obj.getId()).strip())  or \
                  log('Field %r: Object at %r could not be found' % \
                      (self.getName(), r.getURL())) or \
                  r.Title or r.UID) for r, obj in results]
        if not self.required:
            value.insert(0, ('', '<no reference>'))
        return DisplayList(value)

class ComputedField(ObjectField):
    """A field that stores a read-only computation"""
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
        """Return computed value"""
        return eval(self.expression, {'context': instance})

class BooleanField(ObjectField):
    """A field that stores boolean values."""
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'widget' : BooleanWidget,
        })

    def set(self, instance, value, **kwargs):
        """If value is not defined or equal to 0, set field to false;
        otherwise, set to true."""
        if not value or value == '0':
            value = None ## False
        else:
            value = 1

        ObjectField.set(self, instance, value, **kwargs)

class CMFObjectField(ObjectField):
    """
    COMMENT TODO
    """
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
            return self.storage.get(self.getName(), instance, **kwargs)
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
            return info.constructInstance(instance, self.getName(), **kwargs)

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


# ImageField.py
# Written in 2003 by Christian Scholz (cs@comlounge.net)
# version: 1.0 (26/02/2002)
from OFS.Image import Image as BaseImage
from cStringIO import StringIO
try:
    import PIL.Image
    has_pil=1
except:
    # no PIL, no scaled versions!
    has_pil=None

class Image(BaseImage):

    def title(self):
        parent = aq_parent(aq_inner(self))
        if parent is not None:
            return parent.Title() or parent.getId()
        return self.getId()

    title = ComputedAttribute(title, 1)

    alt = title_or_id = title

    def isBinary(self):
        return 1

class ImageField(ObjectField):
    """ implements an image attribute. it stores
        it's data in an image sub-object

        sizes is an dictionary containing the sizes to
        scale the image to. PIL is required for that.

        Format:
        sizes={'mini': (50,50),
               'normal' : (100,100), ... }
        syntax: {'name': (width,height), ... }

        the scaled versions can then be accessed as
        object/<imagename>_<scalename>

        e.g. object/image_mini

        where <imagename> is the fieldname and <scalename>
        is the name from the dictionary

        original_size -- this parameter gives the size in (w,h)
        to which the original image will be scaled. If it's None,
        then no scaling will take place.
        This is important if you don't want to store megabytes of
        imagedata if you only need a max. of 100x100 ;-)

	max_size -- similar to max_size but if it's given then the image
	            is checked to be no bigger than any of the given values
		    of width or height.
		    XXX: I think it is, because the one who added it did not
		    document it ;-) (mrtopf - 2003/07/20)

        example:

        ImageField('image',
            original_size=(600,600),
            sizes={ 'mini' : (80,80),
                    'normal' : (200,200),
                    'big' : (300,300),
                    'maxi' : (500,500)})

        will create an attribute called "image"
        with the sizes mini, normal, big, maxi as given
        and a original sized image of max 600x600.
        This will be accessible as
        object/image

        and the sizes as

        object/image_mini
        object/image_normal
        object/image_big
        object/image_maxi

        Scaling will only be available if PIL is installed!

        If 'DELETE_IMAGE' will be given as value, then all the images
        will be deleted (None is understood as no-op)
        """

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'original_size': None,
        'max_size': None,
        'sizes' : {'thumb':(80,80)},
        'default_content_type' : 'image/gif',
        'allowable_content_types' : ('image/gif','image/jpeg'),
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        })

    default_view = "view"

    def get(self, instance, **kwargs):
        image = ObjectField.get(self, instance, **kwargs)
        if hasattr(image, '__of__') and not kwargs.get('unwrapped', 0):
            return image.__of__(instance)
        return image

    def set(self, instance, value, **kwargs):
##         instance = self.fixInstance(instance)
        # do we have to delete the image?
        if value=="DELETE_IMAGE":
            ObjectField.set(self, instance, None, **kwargs)
            return

        if value == '' or type(value) != StringType:
            image = None
            try:
                image = ObjectField.get(self, instance, **kwargs)
            except AttributeError:
                pass

            # just keep stuff if nothing was uploaded
            if not value: return

            # check for file
            if not ((isinstance(value, FileUpload) and value.filename != '') or
                    (isinstance(value, FileType) and value.name != '')):
                return

            if image:
                #OK, its a file, is it empty?
                value.seek(-1, 2)
                size = value.tell()
                value.seek(0)
                if size == 0:
                 # This new file has no length, so we keep
                 # the orig
                 return

        ###
        ### store the original
        ###

        # test for scaling it.
        imgdata = value
        mimetype = kwargs.get('mimetype', 'image/png')

        if has_pil:
            if self.original_size or self.max_size:
                image = Image(self.getName(), self.getName(), value, mimetype)
                data = str(image.data)
                if self.max_size:
                    if image.width > self.max_size[0] or image.height > self.max_size[1]:
                        factor = min(float(self.max_size[0])/float(image.width),
                                     float(self.max_size[1])/float(image.height))
                        w = int(factor*image.width)
                        h = int(factor*image.height)
                elif self.original_size:
                    w,h = self.original_size
                imgdata = self.scale(data,w,h)

        image = Image(self.getName(), self.getName(), imgdata, mimetype)
        image.filename = hasattr(value, 'filename') and value.filename or ''
        delattr(image, 'title')
        ObjectField.set(self, instance, image, **kwargs)

        # now create the scaled versions
        if not has_pil or not self.sizes:
            return

        data = str(image.data)
        for n, size in self.sizes.items():
            w, h = size
            id = self.getName() + "_" + n
            imgdata = self.scale(data, w, h)
            image2 = Image(id, self.getName(), imgdata, 'image/jpeg')
            # manually use storage
            delattr(image2, 'title')
            self.storage.set(id, instance, image2)


    def scale(self,data,w,h):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        keys = {'height':int(h), 'width':int(w)}

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        image = image.convert('RGB')
        image.thumbnail((keys['width'],keys['height']))
        thumbnail_file = StringIO()
        image.save(thumbnail_file, "JPEG")
        thumbnail_file.seek(0)
        return thumbnail_file.read()

    def getContentType(self, instance):
        img = self.getRaw(instance)
        if img:
            return img.getContentType()
        return ''


class I18NMixIn(ObjectField):
    """ I18N MixIn to allow internationalized content

    this mix in is a litle bit tricky to allow it's use with any other fields.
    You should use it with care !
    class inheriting from this mixin should not be subclassed.
    """
    def __init__(self, name, **kwargs):
        ObjectField.__init__(self, name, **kwargs)
        assert len(self.__class__.__bases__) == 2
        # wrapped field class
        self._wrapped_class = self.__class__.__bases__[-1]
        # this is to avoid the definition of the __init__ method in the
        # subclass just to call the __init__ of the two bases classes. So we
        # call the mixed class __init__ here
        # I know i'm lazy ;)
        self._wrapped_class.__init__(self, name, **kwargs)
        # always store language mapping using the attribute storage
        self._i18n_storage = self.storage
        self.storage = AttributeStorage()
        self._i18n_default = self.default or self._wrapped_class._properties['default']
        self.default = None
        self.type = self.__class__.__name__.lower().replace('field', '')

    def getI18NFieldId(self, lang):
        return '%s__%s'  % (self.__name__, lang)

    def hasI18NContent(self):
        """return true it the field has I18N content"""
        return 1

    def getDefinedLanguages(self, instance):
        """return a list of defined language ids for the given instance"""
        return self._get_mapping(instance).keys()

    def get(self, instance, lang=None, **kwargs):
        lang = getLanguage(instance, lang)
        mapping = self._get_mapping(instance)
        try:
            return mapping[lang].get(instance, **kwargs)
        except KeyError:
            # FIXME : fallback / initialization policy
            master_lang = instance.getMasterLanguage()
            if mapping.has_key(master_lang):
                return mapping[master_lang].get(instance, **kwargs)
            langs = mapping.keys()
            if langs:
                return mapping[langs[0]].get(instance, **kwargs)

            return self._i18n_default

    def getRaw(self, instance, lang=None, **kwargs):
        lang = getLanguage(instance, lang)
        mapping = self._get_mapping(instance)
        try:
            return mapping[lang].getRaw(instance, **kwargs)
        except KeyError:
            return self._i18n_default

    def set(self, instance, value, lang=None, **kwargs):
        value = value or self._i18n_default
        lang = getLanguage(instance, lang)
        mapping = self._get_mapping(instance)
        field = self._build_lang_field(instance, lang)
        field.set(instance, value, **kwargs)
        mapping[lang] = field
        self.storage.set(self.getName(), instance, mapping)

    def unset(self, instance, lang=None, **kwargs):
        lang = getLanguage(instance, lang)
        mapping = self._get_mapping(instance)
        field = mapping.get(lang, None)
        if field:
            field.unset(instance, **kwargs)
        try:
            del mapping[lang]
        except:
            pass

    def setStorage(self, instance, storage):
        if not IStorage.isImplementedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        try:
            value = self.storage.get(self.getName(), instance)
            self.storage.unset(self.getName(), instance)
        except AttributeError:
            value = PersistentMapping()
        self.storage = storage
        if hasattr(self.storage, 'initializeInstance'):
            self.storage.initializeInstance(instance)
        self.storage.set(self.getName(), instance, value)

    def _get_mapping(self, instance):
        try:
            mapping = self.storage.get(self.getName(), instance)
        except AttributeError:
            mapping = None
        if not mapping:
            mapping = PersistentMapping()
            self.storage.set(self.getName(), instance, mapping)
        return mapping

    def _build_lang_field(self, instance, lang):
        dict = copy(self.__dict__)
        dict["storage"] = self._i18n_storage
        dict["default"] = self._i18n_default
        del dict['__name__']
        del dict['_i18n_storage']
        del dict['_i18n_default']
        del dict['storage']
        del dict['_wrapped_class']
        del dict['accessor']
        del dict['edit_accessor']
        del dict['mutator']
        return self._wrapped_class(self.getI18NFieldId(lang), **dict)


class I18NStringField(I18NMixIn, StringField): pass
class I18NFileField(I18NMixIn, FileField): pass
class I18NTextField(I18NMixIn, TextField): pass
class I18NLinesField(I18NMixIn, LinesField): pass
class I18NImageField(I18NMixIn, ImageField): pass

InitializeClass(Field)

# photo field implementation, derived from CMFPhoto by Magnus Heino

from cgi import escape
from cStringIO import StringIO
import sys
from zLOG import LOG, ERROR
from BTrees.OOBTree import OOBTree
from ExtensionClass import Base
from Acquisition import Implicit, aq_parent
from OFS.Traversable import Traversable
from OFS.Image import Image as BaseImage
from OFS.Cache import ChangeCacheSettingsPermission

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

    security.declareProtected(ChangeCacheSettingsPermission, 'ZCacheable_setManagerId')
    def ZCacheable_setManagerId(self, manager_id, REQUEST=None):
        '''Changes the manager_id for this object.
           overridden because we must propagate the change to all variants'''
        for size in self._photos.keys():
            variant = self.getPhoto(size).__of__(self)
            variant.ZCacheable_setManagerId(manager_id)
        return Photo.inheritedAttribute('ZCacheable_setManagerId')(self, manager_id, REQUEST)


InitializeClass(ScalableImage)

class PhotoField(ObjectField):
    """
        A photo field class.
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

InitializeClass(PhotoField)

__all__ = ('Field', 'ObjectField', 'StringField',
           'FileField', 'TextField', 'DateTimeField', 'LinesField',
           'IntegerField', 'FloatField', 'FixedPointField',
           'ReferenceField', 'ComputedField', 'BooleanField',
           'CMFObjectField', 'ImageField',
           'I18NStringField',
           'I18NFileField', 'I18NTextField', 'I18NLinesField',
           'I18NImageField',
           )

from Registry import registerField

registerField(StringField,
              title='String',
              description='Used for storing simple strings')

registerField(FileField,
              title='File',
              description='Used for storing files')

registerField(TextField,
              title='Text',
              description='Used for storing text which can be used in transformations')

registerField(DateTimeField,
              title='Date Time',
              description='Used for storing date/time')

registerField(LinesField,
              title='LinesField',
              description='Used for storing text which can be used in transformations')

registerField(IntegerField,
              title='Integer',
              description='Used for storing integer values')

registerField(FloatField,
              title='Float',
              description='Used for storing float values')

registerField(FixedPointField,
              title='Fixed Point',
              description='Used for storing fixed point values')

registerField(ReferenceField,
              title='Reference',
              description='Used for storing references to other Archetypes Objects')

registerField(ComputedField,
              title='Computed',
              description='Read-only field, which value is computed from a python expression')

registerField(BooleanField,
              title='Boolean',
              description='Used for storing boolean values')

registerField(CMFObjectField,
              title='CMF Object',
              description='Used for storing value inside a CMF Object, which can have workflow. Can only be used for BaseFolder-based content objects')

registerField(ImageField,
              title='Image',
              description='Used for storing images. Images can then be retrieved in different thumbnail sizes')

from Registry import registerPropertyType

registerPropertyType('required', 'boolean')
registerPropertyType('default', 'string')
registerPropertyType('default', 'integer', IntegerField)
registerPropertyType('default', 'boolean', BooleanField)
registerPropertyType('default', 'datetime', DateTimeField)
registerPropertyType('vocabulary', 'string')
registerPropertyType('enforceVocabulary', 'boolean')
registerPropertyType('multiValued', 'boolean', LinesField)
registerPropertyType('searchable', 'boolean')
registerPropertyType('isMetadata', 'boolean')
registerPropertyType('accessor', 'string')
registerPropertyType('edit_accessor', 'string')
registerPropertyType('mutator', 'string')
registerPropertyType('mode', 'string')
registerPropertyType('read_permission', 'string')
registerPropertyType('write_permission', 'string')
registerPropertyType('widget', 'widget')
registerPropertyType('validators', 'validators')
registerPropertyType('index', 'string')
