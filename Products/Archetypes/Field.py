from __future__ import nested_scopes
from copy import deepcopy
from types import ListType, TupleType, ClassType, FileType, DictType
from types import StringType, UnicodeType, IntType

from Products.Archetypes.Layer import DefaultLayerContainer
from Products.Archetypes.config import REFERENCE_CATALOG

from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import IField, IObjectField, \
     IFileField
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces.vocabulary import IVocabulary

from Products.Archetypes.exceptions import ObjectFieldException, \
     TextFieldException, FileFieldException
from Products.Archetypes.Widget import *
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes.ReferenceEngine import Reference
from Products.Archetypes.utils import DisplayList, Vocabulary, className, mapply
from Products.Archetypes.debug import log
from Products.Archetypes import config
from Products.Archetypes.Storage import AttributeStorage, \
     ObjectManagedStorage, ReadOnlyStorage
from Products.Archetypes.Registry import setSecurity, registerField, registerPropertyType

from Products.validation import ValidationChain, UnknowValidatorError, FalseValidatorError
from Products.validation.interfaces.IValidator import IValidator, IValidationChain

import Products.generator.i18n as i18n

from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_base, aq_parent, aq_inner
from DateTime import DateTime
from OFS.content_types import guess_content_type
from OFS.Image import File, Pdata
from Globals import InitializeClass
from ComputedAttribute import ComputedAttribute
from ExtensionClass import Base
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore.utils import getToolByName
from Products.CMFCore import CMFCorePermissions
from ZODB.POSException import ConflictError

from cStringIO import StringIO

STRING_TYPES = [StringType, UnicodeType]
"""String-types currently supported"""

try:
    True
except NameError:
    True=1
    False=0

_marker = []

__docformat__ = 'reStructuredText'

def encode(value, instance, **kwargs):
    """ensure value is an encoded string"""
    if type(value) is type(u''):
        encoding = kwargs.get('encoding')
        if encoding is None:
            try:
                encoding = instance.getCharset()
            except AttributeError:
                # that occurs during object initialization
                # (no acquisition wrapper)
                encoding = 'UTF8'
        value = value.encode(encoding)
    return value

def decode(value, instance, **kwargs):
    """ensure value is an unicode string"""
    if type(value) is type(''):
        encoding = kwargs.get('encoding')
        if encoding is None:
            try:
                encoding = instance.getCharset()
            except AttributeError:
                # that occurs during object initialization
                # (no acquisition wrapper)
                encoding = 'UTF8'
        value = unicode(value, encoding)
    return value

_field_count = 0

class Field(DefaultLayerContainer):
    """
    Extend `DefaultLayerContainer`.
    Implements `IField` and `ILayerContainer` interfaces.
    Class security = public with default access = allow.
    Class attribute _properties is a dictionary containing all of a
    field's property values.
    """

    __implements__ = IField, ILayerContainer

    security = ClassSecurityInfo()

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
        'languageIndependent' : False,
        }

    def __init__(self, name=None, **kwargs):
        """
        Assign name to __name__. Add properties and passed-in
        keyword args to __dict__. Validate assigned validator(s).
        """
        DefaultLayerContainer.__init__(self)

        if name is None:
            global _field_count
            _field_count += 1
            name = 'field.%s' % _field_count

        self.__name__ = name

        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)

        self._widgetLayer()
        self._validationLayer()

        self.registerLayer('storage', self.storage)

    security.declarePrivate('copy')
    def copy(self):
        """
        Return a copy of field instance, consisting of field name and
        properties dictionary.
        """
        cdict = dict(vars(self))
        # Widget must be copied separatedly
        widget = cdict['widget']
        del cdict['widget']
        properties = deepcopy(cdict)
        properties['widget'] = widget.copy()
        return self.__class__(self.getName(), **properties)

    def __repr__(self):
        """
        Return a string representation consisting of name, type and permissions.
        """
        return "<Field %s(%s:%s)>" % (self.getName(), self.type, self.mode)

    def _widgetLayer(self):
        """
        instantiate the widget if a class was given and call
        widget.populateProps
        """
        if hasattr(self, 'widget'):
            if type(self.widget) in (ClassType, type(Base)):
                self.widget = self.widget()
            self.widget.populateProps(self)

    def _validationLayer(self):
        """
        Resolve that each validator is in the service. If validator is
        not, log a warning.

        We could replace strings with class refs and keep things impl
        the ivalidator in the list.

        Note: XXX this is not compat with aq_ things like scripts with __call__
        """
        chainname = 'Validator_%s' % self.getName()

        if type(self.validators) is DictType:
            raise NotImplementedError, 'Please use the new syntax with validation chains'
        elif IValidationChain.isImplementedBy(self.validators):
            validators = self.validators
        elif IValidator.isImplementedBy(self.validators):
            validators = ValidationChain(chainname, validators=self.validators)
        elif type(self.validators) in (TupleType, ListType, StringType):
            if len(self.validators):
                # got a non empty list or string - create a chain
                try:
                    validators = ValidationChain(chainname, validators=self.validators)
                except (UnknowValidatorError, FalseValidatorError), msg:
                    log("WARNING: Disabling validation for %s: %s" % (self.getName(), msg))
                    validators = ()
            else:
                validators = ()
        else:
            log('WARNING: Unknow validation %s. Disabling!' % self.validators)
            validators = ()

        if not self.required:
            if validators == ():
                validators = ValidationChain(chainname)
            if len(validators):
                # insert isEmpty validator at position 0 if first validator
                # is not isEmpty
                if not validators[0][0].name == 'isEmpty':
                    validators.insertSufficient('isEmpty')
            else:
                validators.insertSufficient('isEmpty')

        self.validators = validators

    security.declarePublic('validate')
    def validate(self, value, instance, errors={}, **kwargs):
        """
        Validate passed-in value using all field validators.
        Return None if all validations pass; otherwise, return failed
        result returned by validator
        """
        name = self.getName()
        if errors and errors.has_key(name):
            return 1

        if self.required:
            res = self.validate_required(instance, value, errors)
            if res is not None:
                return res

        if self.enforceVocabulary:
            res = self.validate_vocabulary(instance, value, errors)
            if res is not None:
                return res

        res = instance.validate_field(name, value, errors)
        if res is not None:
            return res

        if self.validators:
            res = self.validate_validators(value, instance, errors, **kwargs)
            if res is not True:
                return res

        # all ok
        return None

    security.declarePrivate('validate_validators')
    def validate_validators(self, value, instance, errors, **kwargs):
        """
        """
        if self.validators:
            result = self.validators(value, instance=instance, errors=errors,
                                     field=self, **kwargs)
        else:
            result = True

        if result is not True:
            return result

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        if not value:
            label = self.widget.Label(instance)
            name = self.getName()
            error = i18n.translate(
                'archetypes', 'error_required',
                {'name': label}, instance,
                default = "%s is required, please correct."
                % label,
                )
            errors[name] = error
            return error
        return None

    security.declarePrivate('validate_vocabulary')
    def validate_vocabulary(self, instance, value, errors):
        """Make sure value is inside the allowed values
        for a given vocabulary"""
        error = None
        if value:
            # coerce value into a list called values
            values = value
            if type(value) in STRING_TYPES:
                values = [value]
            elif type(value) not in (TupleType, ListType):
                raise TypeError("Field value type error: %s" % type(value))
            vocab = self.Vocabulary(instance)
            # filter empty
            values = [instance.unicodeEncode(v)
                      for v in values if v.strip()]
            # extract valid values from vocabulary
            valids = []
            for v in vocab:
                if type(v) in (TupleType, ListType):
                    v = v[0]
                if not type(v) in [type(''), type(u'')]:
                    v = str(v)
                valids.append(instance.unicodeEncode(v))
            # check field values
            for val in values:
                error = 1
                for v in valids:
                    if val == v:
                        error = None
                        break

        if error == 1:
            label = self.widget.Label(instance)
            errors[self.getName()] = error = i18n.translate(
                'archetypes', 'error_vocabulary',
                {'val': val, 'name': label}, instance,
                default = "Value %s is not allowed for vocabulary "
                "of element %s." % (val, label),
                )

        return error

    security.declarePublic('Vocabulary')
    #XXX
    def Vocabulary(self, content_instance=None):
        """
        returns a DisplayList

        uses self.vocabulary as source

        1) Dynamic vocabulary:

            precondition: a content_instance is given.

            has to return a:
                * DisplayList or
                * list of strings or
                * list of 2-tuples with strings:
                    '[("key1","value 1"),("key 2","value 2"),]'

            the output is postprocessed like a static vocabulary.

            vocabulary is a string:
                if a method with the name of the string exists it will be called

            vocabulary is a class implementing IVocabulary:
                the "getDisplayList" method of the class will be called.


        2) Static vocabulary

            * is already a DisplayList
            * is a list of 2-tuples with strings (see above)
            * is a list of strings (in this case a DisplayList with key=value
              will be created)

        """

        value = self.vocabulary
        if not isinstance(value, DisplayList):


            if content_instance is not None and type(value) in STRING_TYPES:
                # dynamic vocabulary by method on class of content_instance
                method = getattr(content_instance, value, None)
                if method and callable(method):
                    args = []
                    kw = {'content_instance' : content_instance,
                          'field' : self}
                    value = mapply(method, *args, **kw)
            elif content_instance is not None and \
                 IVocabulary.isImplementedBy(value):
                # dynamic vocabulary provided by a class that implements
                # IVocabulary
                value=value.getDisplayList(content_instance)

            # Post process value into a DisplayList, templates will use
            # this interface
            sample = value[:1]
            if isinstance(sample, DisplayList):
                # Do nothing, the bomb is already set up
                pass
            elif type(sample) in [TupleType, ListType]:
                # Assume we have ( (value, display), ...)
                # and if not ('', '', '', ...)
                if sample and len(sample[0]) != 2:
                    # if not a 2-tuple
                    value = zip(value, value)
                value = DisplayList(value)
            elif len(sample) and type(sample[0]) == type(''):
                value = DisplayList(zip(value, value))
            else:
                log("Unhandled type in Vocab")
                log(value)

        if content_instance:
            # Translate vocabulary
            i18n_domain = (getattr(self, 'i18n_domain', None) or
                          getattr(self.widget, 'i18n_domain', None))

            return Vocabulary(value, content_instance, i18n_domain)

        return value

    security.declarePublic('checkPermission')
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
            if getattr(sp, 'ext_editor', None) \
                   and self.checkPermission(mode='edit', instance=instance):
                return 1
        return None

    security.declarePublic('getWidgetName')
    def getWidgetName(self):
        """Return the widget name that is configured for this field as
        a string"""
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
    #XXX
    def getDefault(self, instance):
        """Return the default value to be used for initializing this
        field"""
        dm = self.default_method
        if dm:
            if type(dm) is StringType and hasattr(instance, dm):
                method = getattr(instance, dm)
                return method()
            elif callable(dm):
                return dm()
            else:
                raise ValueError('%s.default_method is neither a method of %s'
                                 ' nor a callable' % (self.getName(),
                                                      instance.__class__))
        else:
            return self.default

    security.declarePublic('getAccessor')
    def getAccessor(self, instance):
        """Return the accessor method for getting data out of this
        field"""
        if self.accessor:
            return getattr(instance, self.accessor, None)
        return None

    security.declarePublic('getEditAccessor')
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

    security.declarePrivate('toString')
    def toString(self):
        """Utility method for converting a Field to a string for the
        purpose of comparing fields.  This comparison is used for
        determining whether a schema has changed in the auto update
        function.  Right now it's pretty crude."""
        # XXX fixme
        s = '%s: {' % self.__class__.__name__
        sorted_keys = self._properties.keys()
        sorted_keys.sort()
        for k in sorted_keys:
            s = s + '%s:%s,' % (k, self._properties[k])
        s = s + '}'
        return s

    security.declarePublic('isLanguageIndependent')
    def isLanguageIndependent(self, instance):
        """Get the language independed flag for i18n content
        """
        return self.languageIndependent

    security.declarePublic('getI18nDomain')
    def getI18nDomain(self):
        """ Checks if the user may edit this field and if
        external editor is enabled on this instance """

#InitializeClass(Field)
setSecurity(Field)

class ObjectField(Field):
    """Base Class for Field objects that fundamentaly deal with raw
    data. This layer implements the interface to IStorage and other
    Field Types should subclass this to delegate through the storage
    layer.
    """
    __implements__ = IObjectField, ILayerContainer
    #XXX __implements__ = IField.__implements__, IObjectField

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'default_content_type' : 'application/octet',
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        __traceback_info__ = (self.getName(), instance, kwargs)
        try:
            kwargs['field'] = self
            return self.getStorage(instance).get(self.getName(), instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', 0):
                self.set(instance, self.getDefault(instance), _initializing_=1, **kwargs)
            return self.getDefault(instance)

    security.declarePrivate('getRaw')
    def getRaw(self, instance, **kwargs):
        if self.accessor is not None:
            accessor = self.getAccessor(instance)
        else:
            # self.accessor is None for fields wrapped by an I18NMixIn
            accessor = None
        kwargs.update({'field': self.getName(),
                       'encoding':kwargs.get('encoding', None),
                     })
        if accessor is None:
            args = [instance,]
            return mapply(self.get, *args, **kwargs)
        return mapply(accessor, **kwargs)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        kwargs['mimetype'] = kwargs.get('mimetype', getattr(self, 'default_content_type', 'application/octet'))
        # Remove acquisition wrappers
        value = aq_base(value)
        __traceback_info__ = (self.getName(), instance, value, kwargs)
        self.getStorage(instance).set(self.getName(), instance, value, **kwargs)

    security.declarePrivate('unset')
    def unset(self, instance, **kwargs):
        #kwargs['field'] = self
        __traceback_info__ = (self.getName(), instance, kwargs)
        self.getStorage(instance).unset(self.getName(), instance, **kwargs)

    security.declarePrivate('setStorage')
    def setStorage(self, instance, storage):
        if not IStorage.isImplementedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        # raw=1 is required for TextField
        value = self.get(instance, raw=1)
        self.unset(instance)
        self.storage = storage
        if hasattr(self.storage, 'initializeInstance'):
            self.storage.initializeInstance(instance)
        self.set(instance, value)

    security.declarePrivate('getStorage')
    def getStorage(self, instance=None):
        return self.storage

    security.declarePublic('getStorageName')
    def getStorageName(self, instance=None):
        """Return the storage name that is configured for this field
        as a string"""
        return self.getStorage(instance).getName()

    security.declarePublic('getStorageType')
    def getStorageType(self, instance=None):
        """Return the type of the storage of this field as a string"""
        return className(self.getStorage(instance))

    #XXX security.declareProtected(CMFCorePermissions.AccessPortalContent, 'getContentType')
    security.declarePublic('getContentType')
    def getContentType(self, instance, fromBaseUnit=True):
        """Return the mime type of object if known or can be guessed;
        otherwise, return None."""
        value = ''
        if fromBaseUnit and hasattr(self, 'getBaseUnit'):
            bu = self.getBaseUnit(instance)
            if IBaseUnit.isImplementedBy(bu):
                return str(bu.getContentType())
        raw = self.getRaw(instance)
        mimetype = getattr(aq_base(raw), 'mimetype', None)
        # some instances like OFS.Image have a getContentType method
        if mimetype is None:
            getCT = getattr(raw, 'getContentType', None)
            if callable(getCT):
                mimetype = getCT()
        # try to guess
        if mimetype is None:
            mimetype, enc = guess_content_type('', str(raw), None)
        else:
            # mimetype may be an imimetype object
            mimetype = str(mimetype)
        # failed
        if mimetype is None:
            mimetype = getattr(self, 'default_content_type', 'application/octet')
        return mimetype

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        
        Should be overwritte by special fields like FileField. It's safe for
        fields which are storing strings, ints and BaseUnits but it won't return
        the right results for fields containing OFS.Image.File instances or
        lists/tuples/dicts.
        """
        data = self.getRaw(instance)
        try:
            return len(data)
        except (TypeError, AttributeError):
            return len(str(data))

#InitializeClass(ObjectField)
setSecurity(ObjectField)

class StringField(ObjectField):
    """A field that stores strings"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'string',
        'default': '',
        'default_content_type' : 'text/plain',
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        return encode(value, instance, **kwargs)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        # Remove acquisition wrappers
        value = decode(aq_base(value), instance, **kwargs)
        self.getStorage(instance).set(self.getName(), instance, value, **kwargs)

class FileField(ObjectField):
    """Something that may be a file, but is not an image and doesn't
    want text format conversion"""

    __implements__ = IFileField, ILayerContainer
    #XXX __implements__ = IFileField, IObjectField.__implements__

    _properties = ObjectField._properties.copy()
    _properties.update({
        'type' : 'file',
        'default' : '',
        'primary' : 0,
        'widget' : FileWidget,
        'content_class' : File,
        'default_content_type' : 'application/octet',
        })

    security  = ClassSecurityInfo()

    def _process_input(self, value, default=None,
                       mimetype=None, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if not (isinstance(value, FileUpload) or type(value) is FileType) \
          and hasattr(value, 'read') and hasattr(value, 'seek'):
            # support StringIO and other file like things that aren't either
            # files or FileUploads
            value.seek(0) # rewind
            kwargs['filename'] = getattr(value, 'filename', '')
            mimetype = getattr(value, 'mimetype', None)
            value = value.read()
        if isinstance(value, Pdata):
            # Pdata is a chain of Pdata objects but we can easily use str()
            # to get the whole string from a chain of Pdata objects
            value = str(value)
        if type(value) in STRING_TYPES:
            filename = kwargs.get('filename', '')
            if mimetype is None:
                mimetype, enc = guess_content_type(filename, value, mimetype)
            if not value:
                return default, mimetype, filename
            return value, mimetype, filename
        elif IBaseUnit.isImplementedBy(value):
            return value.getRaw(), value.getContentType(), value.getFilename()

        value = aq_base(value)

        if ((isinstance(value, FileUpload) and value.filename != '') or
              (type(value) is FileType and value.name != '')):
            filename = ''
            if isinstance(value, FileUpload) or hasattr(value, 'filename'):
                filename = value.filename
            if isinstance(value, FileType) or hasattr(value, 'name'):
                filename = value.name
            # Get only last part from a 'c:\\folder\\file.ext'
            filename = filename.split('\\')[-1]
            value = value.read()
            if mimetype is None:
                mimetype, enc = guess_content_type(filename, value, mimetype)
            size = len(value)
            if size == 0:
                # This new file has no length, so we keep the orig
                return default, mimetype, filename
            else:
                return value, mimetype, filename

        if isinstance(value, File):
            # OFS.Image.File based
            filename = value.filename
            mimetype = value.content_type
            data = value.data
            if len(data) == 0:
                return default, mimetype, filename
            else:
                return data, mimetype, filename

        klass = getattr(value, '__class__', None)
        raise FileFieldException('Value is not File or String (%s - %s)' %
                                 (type(value), klass))

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        if hasattr(value, '__of__') and not kwargs.get('unwrapped', False):
            return value.__of__(instance)
        else:
            return value

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """
        Assign input value to object. If mimetype is not specified,
        pass to processing method without one and add mimetype returned
        to kwargs. Assign kwargs to instance.
        """
        if not value:
            return

        if not kwargs.has_key('mimetype'):
            kwargs['mimetype'] = None

        value, mimetype, filename = self._process_input(value,
                                                      default=self.getDefault(instance),
                                                      **kwargs)
        kwargs['mimetype'] = mimetype
        kwargs['filename'] = filename

        if value=="DELETE_FILE":
            if hasattr(aq_base(instance), '_FileField_types'):
                delattr(aq_base(instance), '_FileField_types')
            ObjectField.unset(self, instance, **kwargs)
            return

        # remove ugly hack
        if hasattr(aq_base(instance), '_FileField_types'):
            del instance._FileField_types
        if value is None:
            # do not send None back as file value if we get a default (None)
            # value back from _process_input.  This prevents
            # a hard error (NoneType object has no attribute 'seek') from
            # occurring if someone types in a bogus name in a file upload
            # box (at least under Mozilla).
            value = ''
        obj = self._wrapValue(instance, value, **kwargs)
        ObjectField.set(self, instance, obj, **kwargs)

    def _wrapValue(self, instance, value, **kwargs):
        """Wraps the value in the content class if it's not wrapped
        """
        if isinstance(value, self.content_class):
            return value

        mimetype = kwargs.get('mimetype', self.default_content_type)
        filename = kwargs.get('filename', '')

        obj = self.content_class(self.getName(), '', str(value), mimetype)
        setattr(obj, 'filename', filename) # filename or self.getName())
        setattr(obj, 'content_type', mimetype)
        delattr(obj, 'title')
        
        return obj

    security.declarePrivate('getBaseUnit')
    def getBaseUnit(self, instance):
        """Return the value of the field wrapped in a base unit object
        """
        filename = self.getFilename(instance, fromBaseUnit=False)
        if not filename:
            filename = '' # self.getName()
        mimetype = self.getContentType(instance, fromBaseUnit=False)
        value = self.getRaw(instance) or self.getDefault(instance)
        if isinstance(aq_base(value), File):
            value = str(aq_base(value).data)
        bu = BaseUnit(filename, aq_base(value), instance,
                      filename=filename, mimetype=mimetype)
        return bu

    security.declarePublic('getFileName') # XXX
    def getFilename(self, instance, fromBaseUnit=True):
        """Get file name of underlaying file object
        """
        filename = None
        if fromBaseUnit:
            bu = self.getBaseUnit(instance)
            return bu.getFilename()
        raw = self.getRaw(instance)
        filename = getattr(aq_base(raw), 'filename', None)
        # for OFS.Image.*
        if filename is None:
            filename = getattr(raw, 'filename', None)
        # might still be None
        if filename:
            # taking care of stupid IE and be backward compatible
            # BaseUnit hasn't have a fix for long so we might have an old name
            filename = filename.split("\\")[-1]
        return filename

    security.declarePrivate('setFilename')
    def setFilename(self, instance, filename):
        """Set file name in the base unit [PRIVATE]
        """
        bu = self.getBaseUnit(instance)
        bu.setFilename(filename)

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = getattr(value, 'get_size', lambda: value and str(value))()
        return ObjectField.validate_required(self, instance, value, errors)

    security.declarePrivate('download')
    def download(self, instance, REQUEST=None, RESPONSE=None):
        """Kicks download [PRIVATE]

        Writes data including file name and content type to RESPONSE
        """
        bu = self.getBaseUnit(instance)
        if not REQUEST:
            REQUEST = instance.REQUEST
        if not RESPONSE:
            RESPONSE = REQUEST.RESPONSE
        return bu.index_html(REQUEST, RESPONSE)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return len(str(self.get(instance)))

class TextField(FileField):
    """Base Class for Field objects that rely on some type of
    transformation"""

    __implements__ = FileField.__implements__

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'text',
        'default' : '',
        'widget': StringWidget,
        'default_content_type' : 'text/plain',
        'default_output_type'  : 'text/plain',
        'allowable_content_types' : ('text/plain',),
        'primary' : 0,
        })

    security  = ClassSecurityInfo()

    security.declarePublic('defaultView')
    def defaultView(self):
        return self.default_output_type

    def _process_input(self, value, default=None, mimetype=None, **kwargs):
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

        raise TextFieldException(('Value is not File, String or '
                                  'BaseUnit on %s: %r' % (self.getName(),
                                                          type(value))))

    security.declarePrivate('getRaw')
    def getRaw(self, instance, raw=0, **kwargs):
        """
        If raw, return the base unit object, else return encoded raw data
        """
        value = self.get(instance, raw=1, **kwargs)
        if raw or not IBaseUnit.isImplementedBy(value):
            return value
        kw = {'encoding':kwargs.get('encoding'),
              'instance':instance}
        args = []
        return mapply(value.getRaw, *args, **kw)

    security.declarePrivate('get')
    def get(self, instance, mimetype=None, raw=0, **kwargs):
        """ If raw, return the base unit object, else return value of
        object transformed into requested mime type.

        If no requested type, then return value in default type. If raw
        format is specified, try to transform data into the default output type
        or to plain text.
        If we are unable to transform data, return an empty string. """
        try:
            kwargs['field'] = self
            value = self.getStorage(instance).get(self.getName(), instance, **kwargs)
            if not IBaseUnit.isImplementedBy(value):
                return encode(value, instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', 0):
                self.set(instance, self.getDefault(instance), _initializing_=1, **kwargs)
            return self.getDefault(instance)

        if raw:
            return value

        if mimetype is None:
            mimetype = self.default_output_type or 'text/plain'

        if not hasattr(value, 'transform'): # oldBaseUnits have no transform
            return str(value)
        data = value.transform(instance, mimetype)
        if not data and mimetype != 'text/plain':
            data = value.transform(instance, 'text/plain')
        return data or ''

    security.declarePrivate('getBaseUnit')
    def getBaseUnit(self, instance):
        """Return the value of the field wrapped in a base unit object
        """
        return self.get(instance, raw=1)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """ Assign input value to object. If mimetype is not specified,
        pass to processing method without one and add mimetype
        returned to kwargs. Assign kwargs to instance.
        """
        if value is None:
            # nothing to do
            return

        value = self._process_input(value, default=self.getDefault(instance), **kwargs)
        encoding = kwargs.get('encoding')
        if type(value) is type(u'') and encoding is None:
            encoding = 'UTF-8'

        # fix for external editor support
        # set mimetype to the last state if the mimetype in kwargs is None or 'None'
        mimetype = kwargs.get('mimetype', None)
        if mimetype == 'None':
            kwargs['mimetype'] = self.getContentType(instance)

        if not IBaseUnit.isImplementedBy(value):
            value = BaseUnit(self.getName(), value, instance=instance,
                             encoding=encoding,
                             mimetype=kwargs.get('mimetype'),
                             filename=kwargs.get('filename', ''))

        ObjectField.set(self, instance, value, **kwargs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return len(self.getBaseUnit(instance))


class DateTimeField(ObjectField):
    """A field that stores dates and times"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
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
            except: #XXX bare exception
                value = None

        ObjectField.set(self, instance, value, **kwargs)

class LinesField(ObjectField):
    """For creating lines objects"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'lines',
        'default' : (),
        'widget' : LinesWidget,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """
        If passed-in value is a string, split at line breaks and
        remove leading and trailing white space before storing in object
        with rest of properties.
        """
        __traceback_info__ = value, type(value)
        if type(value) in STRING_TYPES:
            value =  value.split('\n')
        value = [decode(v.strip(), instance, **kwargs)
                 for v in value if v and v.strip()]
        if config.ZOPE_LINES_IS_TUPLE_TYPE:
            value = tuple(value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs) or ()
        if config.ZOPE_LINES_IS_TUPLE_TYPE:
            return tuple([encode(v, instance, **kwargs) for v in value])
        else:
            return [encode(v, instance, **kwargs) for v in value]

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        size=0
        for line in self.get(instance):
            size+=len(str(line))
        return size


class IntegerField(ObjectField):
    """A field that stores an integer"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer',
        'size' : '10',
        'widget' : IntegerWidget,
        'default' : 0
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
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

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
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
        'default' : '0.00',
        'widget' : DecimalWidget,
        'validators' : ('isDecimal'),
        })

    security  = ClassSecurityInfo()

    def _to_tuple(self, instance, value):
        """ COMMENT TO-DO """
        if not value:
            value = self.getDefault(instance)
        value = value.split('.')
        __traceback_info__ = (self, value)
        if len(value) < 2:
            value = (int(value[0]), 0)
        else:
            fra = value[1][:self.precision]
            fra += '0' * (self.precision - len(fra))
            value = (int(value[0]), int(fra))
        return value

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        value = self._to_tuple(instance, value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        template = '%%d.%%0%dd' % self.precision
        value = ObjectField.get(self, instance, **kwargs)
        __traceback_info__ = (template, value)
        if value is None: return self.getDefault(instance)
        if type(value) in [StringType]: value = self._to_tuple(instance, value)
        return template % value

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = sum(self._to_tuple(instance, value))
        return ObjectField.validate_required(self, instance, value, errors)

class ReferenceField(ObjectField):
    __implements__ = ObjectField.__implements__

    """A field for creating references between objects.

    get() returns the list of objects referenced under the relationship
    set() converts a list of target UIDs into references under the
    relationship associated with this field.

    If no vocabulary is provided by you, one will be assembled based on
    allowed_types.
    """

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'reference',
        'default' : None,
        'widget' : ReferenceWidget,

        'relationship' : None, # required
        'allowed_types' : (),  # a tuple of portal types, empty means allow all
        'allowed_types_method' :None,
        'vocabulary_display_path_bound': 5, # if len(vocabulary) > 5, we'll
                                            # display path as well
        'vocabulary_custom_label': None, # e.g. "b.getObject().title_or_id()".
                                         # if given, this will
                                         # override display_path_bound
        'referenceClass' : Reference,
        'referenceReferences' : False,
        'callStorageOnSet': False,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, aslist=0, **kwargs):
        """get() returns the list of objects referenced under the relationship
        """
        res=instance.getRefs(relationship=self.relationship)

        #singlevalued ref fields return only the object, not a list,
        #unless explicitely specified by the aslist option
        if not self.multiValued and not aslist:
            if res:
                assert len(res) == 1
                res=res[0]
            else:
                res=None

        return res

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """Mutator.

        ``value`` is a list of UIDs or one UID string to which I will add a
        reference to. None and [] are equal.

        Keyword arguments may be passed directly to addReference(), thereby
        creating properties on the reference objects.
        """
        tool = getToolByName(instance, REFERENCE_CATALOG)
        targetUIDs = [ref.targetUID for ref in
                      tool.getReferences(instance, self.relationship)]

        if not self.multiValued and value and type(value) not in (type(()),type([])):
            value = (value,)

        if not value:
            value = ()

        #convertobjects to uids if necessary
        uids=[]
        for v in value:
            if type(v) in (type(''),type(u'')):
                uids.append(v)
            else:
                uids.append(v.UID())

        add = [v for v in uids if v and v not in targetUIDs]
        sub = [t for t in targetUIDs if t not in uids]

        # tweak keyword arguments for addReference
        addRef_kw = kwargs.copy()
        addRef_kw.setdefault('referenceClass', self.referenceClass)
        if addRef_kw.has_key('schema'): del addRef_kw['schema']

        for uid in add:
            __traceback_info__ = (instance, uid, value, targetUIDs)
            # throws IndexError if uid is invalid
            tool.addReference(instance, uid, self.relationship, **addRef_kw)

        for uid in sub:
            tool.deleteReference(instance, uid, self.relationship)

        if self.callStorageOnSet:
            #if this option is set the reference fields's values get written
            #to the storage even if the reference field never use the storage
            #e.g. if i want to store the reference UIDs into an SQL field
            ObjectField.set(self, instance, self.getRaw(instance), **kwargs)

    security.declarePrivate('getRaw')
    def getRaw(self, instance, aslist=0, **kwargs):
        """Return the list of UIDs referenced under this fields
        relationship
        """
        rc = getToolByName(instance, REFERENCE_CATALOG)
        brains = rc(sourceUID=instance.UID(),
                    relationship=self.relationship)
        res = [b.targetUID for b in brains]
        if not self.multiValued and not aslist:
            if res:
                res = res[0]
            else:
                res = None
        return res

    security.declarePublic('Vocabulary')
    def Vocabulary(self, content_instance=None):
        """Use vocabulary property if it's been defined."""
        if self.vocabulary:
            return ObjectField.Vocabulary(self, content_instance)
        else:
            return self._Vocabulary(content_instance).sortedByValue()

    def _Vocabulary(self, content_instance):
        pairs = []
        pc = getToolByName(content_instance, 'portal_catalog')
        uc = getToolByName(content_instance, config.UID_CATALOG)

        allowed_types=self.allowed_types
        allowed_types_method=getattr(self,'allowed_types_method',None)
        if allowed_types_method:
            meth=getattr(content_instance,allowed_types_method)
            allowed_types=meth(self)

        skw = allowed_types and {'portal_type':allowed_types} or {}
        brains = uc.searchResults(**skw)

        if self.vocabulary_custom_label is not None:
            label = lambda b:eval(self.vocabulary_custom_label, {'b': b})
        elif len(brains) > self.vocabulary_display_path_bound:
            at = i18n.translate(domain='archetypes', msgid='label_at',
                                context=content_instance, default='at')
            label = lambda b:'%s %s %s' % (b.Title or b.id, at,
                                           b.getPath())
        else:
            label = lambda b:b.Title or b.id

        # The UID catalog is the correct catalog to pull this
        # information from, however the workflow and perms are not accounted
        # for there. We thus check each object in the portal catalog
        # to ensure it validity for this user.
        portal_base = getToolByName(content_instance,'portal_url').getPortalPath()
        path_offset = len(getToolByName(content_instance,'portal_url').getPortalPath())+1
        abs_paths = {}
        def assign(x, y): abs_paths[x]=y
        [assign("%s/%s" %(portal_base, b.getPath()), b) for b in brains]
        #[assign("%s" %(b.getPath()), b) for b in brains]

        pc_brains = pc(path=abs_paths.keys(), **skw)

        for b in pc_brains:
            #translate abs path to rel path since uid_cat stores paths relative now
            path=b.getPath()[path_offset:]
            # The reference field will not expose Refrerences by
            # default, this is a complex use-case and makes things too hard to
            # understand for normal users. Because of reference class
            # we don't know portal type but we can look for the annotation key in
            # the path
            if self.referenceReferences is False and \
               path.find(config.REFERENCE_ANNOTATION) != -1:
                continue

            # now check if the results from the pc is the same as in uc.
            # so we verify that b is a result that was also returned by uc,
            # hence the check in abs_paths.
            if abs_paths.has_key(b.getPath()):
                pairs.append((abs_paths[b.getPath()].UID, label(b)))
         
        if not self.required and not self.multiValued:
            no_reference = i18n.translate(domain='archetypes',
                                          msgid='label_no_reference',
                                          context=content_instance,
                                          default='<no reference>')
            pairs.insert(0, ('', no_reference))

        return DisplayList(pairs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 0


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

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, *ignored, **kwargs):
        pass

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        """Return computed value"""
        return eval(self.expression, {'context': instance, 'here' : instance})

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 0

class BooleanField(ObjectField):
    """A field that stores boolean values."""
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'widget' : BooleanWidget,
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """If value is not defined or equal to 0, set field to false;
        otherwise, set to true."""
        if not value or value == '0':
            value = None ## False
        else:
            value = 1

        ObjectField.set(self, instance, value, **kwargs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 1

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
        'widget' : FileWidget,
        'storage': ObjectManagedStorage(),
        'workflowable': 1,
        })

    security  = ClassSecurityInfo()

    def _process_input(self, value, default=None, **kwargs):
        __traceback_info__ = (value, type(value))
        if type(value) != StringType:
            if ((isinstance(value, FileUpload) and value.filename != '') or \
                (isinstance(value, FileType) and value.name != '')):
                # OK, its a file, is it empty?
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

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        try:
            return self.getStorage(instance).get(self.getName(), instance, **kwargs)
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
            args = [instance, self.getName()]
            for k in ['field', 'schema']:
                del kwargs[k]
            return mapply(info.constructInstance, *args, **kwargs)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        obj = self.get(instance, **kwargs)
        value = self._process_input(value, default=self.getDefault(instance), \
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
try:
    import PIL.Image
    has_pil=1
except ImportError:
    # no PIL, no scaled versions!
    log("Warning: no Python Imaging Libraries (PIL) found."+\
        "Archetypes based ImageField's don't scale if neccessary.")
    has_pil=None

class Image(BaseImage):

    security  = ClassSecurityInfo()

    def title(self):
        parent = aq_parent(aq_inner(self))
        if parent is not None:
            return parent.Title() or parent.getId()
        return self.getId()

    title = ComputedAttribute(title, 1)

    alt = title_or_id = title

    def isBinary(self):
        return 1

class ImageField(FileField):
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

        sizes may be the name of a method in the instance or a callable which
        returns a dict.

        Scaling will only be available if PIL is installed!

        If 'DELETE_IMAGE' will be given as value, then all the images
        will be deleted (None is understood as no-op)
        """

    # XXX__implements__ = FileField.__implements__ , IImageField

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'original_size': None,
        'max_size': None,
        'sizes' : {'thumb':(80,80)},
        'default_content_type' : 'image/png',
        'allowable_content_types' : ('image/gif','image/jpeg','image/png'),
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        'content_class': Image,
        })

    security  = ClassSecurityInfo()

    default_view = "view"

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        if not value:
            return

        # Do we have to delete the image?
        if value=="DELETE_IMAGE":
            self.removeScales(instance, **kwargs)
            # unset main field too
            ObjectField.unset(self, instance, **kwargs)
            return

        if not kwargs.has_key('mimetype'):
            kwargs['mimetype'] = None

        value, mimetype, filename = self._process_input(value,
                                                      default=self.getDefault(instance),
                                                      **kwargs)
        #print type(value), mimetype, filename

        kwargs['mimetype'] = mimetype
        kwargs['filename'] = filename

##        if value == '' or type(value) != StringType:
##            image = None
##            try:
##                image = ObjectField.get(self, instance, **kwargs)
##            except AttributeError:
##                pass
##
##            # just keep stuff if nothing was uploaded
##            if not value: return
##
##            # check for file
##            if not ((isinstance(value, FileUpload) and value.filename != '') or
##                    (isinstance(value, FileType) and value.name != '')):
##                return
##
##            if image:
##                #OK, its a file, is it empty?
##                value.seek(-1, 2)
##                size = value.tell()
##                value.seek(0)
##                if size == 0:
##                    # This new file has no length, so we keep
##                    # the orig
##                    return

        kwargs = self._updateKwargs(instance, value, **kwargs)
        imgdata = self.rescaleOriginal(value, **kwargs)
        # XXX add self.ZCacheable_invalidate() later
        self.createOriginal(instance, imgdata, **kwargs)
        self.createScales(instance)

    def _updateKwargs(self, instance, value, **kwargs):
        # get filename from kwargs, then from the value
        # if no filename is available set it to ''
        vfilename = getattr(value, 'filename', '')
        kfilename = kwargs.get('filename', '')
        if kfilename:
            filename = kfilename
        else:
            filename = vfilename
        kwargs['filename'] = filename

        # set mimetype from kwargs, then from the field itself
        # if no mimetype is available set it to 'image/png'
        kmimetype = kwargs.get('mimetype', None)
        imimetype = self.getContentType(instance)
        if kmimetype:
            mimetype = kmimetype
        elif imimetype:
            mimetype = imimetype
        else:
            mimetype = 'image/png'
        kwargs['mimetype'] = mimetype
        return kwargs

    security.declareProtected(CMFCorePermissions.View, 'getAvailableSizes')
    def getAvailableSizes(self, instance):
        """Get sizes

        Supports:
            self.sizes as dict
            A method in instance called like sizes that returns dict
            A callable
        """
        sizes = self.sizes
        if type(sizes) is DictType:
            return sizes
        elif type(sizes) is StringType:
            assert(hasattr(aq_base(instance), sizes))
            method = getattr(instances, sizes)
            data = method()
            assert(type(data) is DictType)
            return data
        elif callable(sizes):
            return sizes()
        else:
            raise TypeError, 'Wrong self.sizes has wrong type' % type(sizes)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'rescaleOriginal')
    def rescaleOriginal(self, value, **kwargs):
        """rescales the original image and sets the data

        for self.original_size or self.max_size
        """
        mimetype = kwargs.get('mimetype', 'image/png')
        if has_pil:
            if self.original_size or self.max_size:
                image = self.content_class(self.getName(), self.getName(),
                                         value, mimetype)
                data = str(image.data)
                w=h=0
                if self.max_size:
                    if image.width > self.max_size[0] or \
                           image.height > self.max_size[1]:
                        factor = min(float(self.max_size[0])/float(image.width),
                                     float(self.max_size[1])/float(image.height))
                        w = int(factor*image.width)
                        h = int(factor*image.height)
                elif self.original_size:
                    w,h = self.original_size
                if w and h:
                    fvalue, format = self.scale(data,w,h)
                    value = fvalue.read()
        return value

    security.declarePrivate('createOriginal')
    def createOriginal(self, instance, value, **kwargs):
        """create the original image (save it)
        """
        image = self._wrapValue(instance, value, **kwargs)

        ObjectField.set(self, instance, image, **kwargs)

    security.declarePrivate('removeScales')
    def removeScales(self, instance, **kwargs):
        """Remove the scaled image
        """
        sizes = self.getAvailableSizes(instance)
        if sizes:
            for name, size in sizes.items():
                id = self.getName() + "_" + name
                try:
                    # the following line may throw exceptions on types, if the
                    # type-developer add sizes to a field in an existing
                    # instance and a user try to remove an image uploaded before
                    # that changed. The problem is, that the behavior for non
                    # existent keys isn't defined. I assume a keyerror will be
                    # thrown. Ignore that.
                    self.getStorage(instance).unset(id, instance, **kwargs)
                except KeyError:
                    pass

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'createScales')
    def createScales(self, instance):
        """creates the scales and save them
        """
        sizes = self.getAvailableSizes(instance)
        if not has_pil or not sizes:
            return
        img = self.getRaw(instance)
        if not img:
            return
        data = str(img.data)
        for n, size in sizes.items():
            w, h = size
            id = self.getName() + "_" + n
            imgdata, format = self.scale(data, w, h)
            image = self.content_class(id, self.getName(),
                                     imgdata,
                                     'image/%s' % format
                                     )
            # manually use storage
            delattr(image, 'title')
            self.getStorage(instance).set(id, instance, image)

    security.declarePrivate('scale')
    def scale(self, data, w, h):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        size = int(w), int(h)

        pilfilter = PIL.Image.NEAREST
        #check for the pil version and enable antialias if > 1.1.3
        if PIL.Image.VERSION >= "1.1.3":
            pilfilter = PIL.Image.ANTIALIAS

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        # consider image mode when scaling
        # source images can be mode '1','L,','P','RGB(A)'
        # convert to greyscale or RGBA before scaling
        # preserve palletted mode (but not pallette)
        # for palletted-only image formats, e.g. GIF
        # PNG compression is OK for RGBA thumbnails
        original_mode = image.mode
        if original_mode == '1':
            image = image.convert('L')
        elif original_mode == 'P':
            image = image.convert('RGBA')
        image.thumbnail(size, pilfilter)
        # XXX: tweak to make the unit test
        #      test_fields.ProcessingTest.test_processing_fieldset run
        format = image.format and image.format or 'PNG'
        # decided to only preserve palletted mode
        # for GIF, could also use   image.format in ('GIF','PNG')
        if original_mode == 'P' and format == 'GIF':
            image = image.convert('P')
        thumbnail_file = StringIO()
        # quality parameter doesn't affect lossless formats
        image.save(thumbnail_file, format, quality=88)
        thumbnail_file.seek(0)
        return thumbnail_file, format.lower()
    
    security.declareProtected(CMFCorePermissions.View, 'getSize')
    def getSize(self, instance, scale=None):
        """get size of scale or original
        """
        img = self.getScale(instance, scale=scale)
        return img.width, img.height
        
    security.declareProtected(CMFCorePermissions.View, 'getScale')
    def getScale(self, instance, scale=None, **kwargs):
        """Get scale by name or original
        """
        if scale is None:
            return self.get(instance, **kwargs)
        else:
            assert(scale in self.getAvailableSizes(instance).keys(),
                   'Unknown scale %s for %s' % (scale, self.getName()))
            id = self.getScaleName(scale=scale)
            image = self.getStorage(instance).get(id, instance, **kwargs)
            image = self._wrapValue(instance, image, **kwargs)
            if hasattr(image, '__of__') and not kwargs.get('unwrapped', False):
                return image.__of__(instance)
            else:
                return image

    security.declareProtected(CMFCorePermissions.View, 'getScaleName')
    def getScaleName(self, scale=None):
        """Get the full name of the attribute for the scale
        """
        if scale:
            return self.getName() + "_" + scale
        else:
            return ''

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        sizes = self.getAvailableSizes(instance)
        size=0
        size+=len(str(self.get(instance)))
        
        if sizes:
            for name in sizes.keys():
                id = self.getScaleName(scale=name)        
                try:
                    data = self.getStorage(instance).get(id, instance)
                except AttributeError:
                    pass
                else:
                    size+=len(str(data))
        return size

    security.declareProtected(CMFCorePermissions.View, 'tag')
    def tag(self, instance, scale=None, height=None, width=None, alt=None,
            css_class=None, title=None, **kwargs):
        """Create a tag including scale
        """
        image = self.getScale(instance, scale=scale)

        if height is None:
            height=image.height
        if width is None:
            width=image.width

        url = instance.absolute_url()
        if scale:
            url+='/' + self.getScaleName(scale)
            
        values = {'src' : url,
                  'alt' : alt and alt or instance.Title(),
                  'title' : title and title or instance.Title(),
                  'height' : height,
                  'width' : width,
                 } 
        
        result = '<img src="%(src)s" alt="%(alt)s" title="%(title)s" '\
                 'widht="%(width)s" height="%(height)s"' % values

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key, value in kwargs.items():
            if value:
                result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

# photo field implementation, derived from CMFPhoto by Magnus Heino

from cgi import escape
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
    """Provide a transparent wrapper from image to dynvariant call it
    with url ${image_url}/variant/${variant}
    """

    def __of__(self, parent):
        return parent.Variants()

class DynVariant(Implicit, Traversable):
    """Provide access to the variants."""

    def __init__(self):
        pass

    def __getitem__(self, name):
        if self.checkForVariant(name):
            return self.getPhoto(name).__of__(aq_parent(self))
        else:
            return aq_parent(self)

class ScalableImage(BaseImage):
    """A scalable image class."""

    __implements__ = BaseImage.__implements__

    meta_type = 'Scalable Image'

    isBinary = lambda self: 1

    security  = ClassSecurityInfo()

    def __init__(self, id, title='', file='', displays={}):
        BaseImage.__init__(self, id, title, file)
        self._photos = OOBTree()
        self.displays = displays

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
        """Return an HTML img tag (See OFS.Image)"""

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
                    imgin, imgout = popen2(('convert -quality %s '
                                            '-geometry %sx%s - -'
                                            % (quality, width, height), 'b'))
                else:
                    from popen2 import Popen3
                    convert=Popen3(('convert -quality %s '
                                    '-geometry %sx%s - -'
                                    % (quality, width, height)))
                    imgout=convert.fromchild
                    imgin=convert.tochild

                imgin.write(str(self.data))
                imgin.close()
                image.write(imgout.read())
                imgout.close()

                # Wait for process to close if unix.
                # Should check returnvalue for wait
                if sys.platform !='win32':
                    convert.wait()

                image.seek(0)

        except ConflictError:
            raise
        except Exception, e:
            LOG('Archetypes.ScallableField', ERROR,
                'Error while resizing image', e)

        return image

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setManagerId')
    def ZCacheable_setManagerId(self, manager_id, REQUEST=None):
        '''Changes the manager_id for this object.
           overridden because we must propagate the change to all variants'''
        for size in self._photos.keys():
            variant = self.getPhoto(size).__of__(self)
            variant.ZCacheable_setManagerId(manager_id)
        inherited_attr = Photo.inheritedAttribute('ZCacheable_setManagerId')
        return inherited_attr(self, manager_id, REQUEST)


InitializeClass(ScalableImage)

class PhotoField(ObjectField):
    """A photo field class."""

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

    security  = ClassSecurityInfo()

    default_view = "view"

    security.declarePrivate('set')
    def set(self, instance, value, **kw):
        if type(value) is StringType:
            value = StringIO(value)
        image = ScalableImage(self.getName(), file=value,
                              displays=self.displays)
        ObjectField.set(self, instance, image, **kw)

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = getattr(value, 'get_size', lambda: str(value))()
        return ObjectField.validate_required(self, instance, value, errors)

__all__ = ('Field', 'ObjectField', 'StringField',
           'FileField', 'TextField', 'DateTimeField', 'LinesField',
           'IntegerField', 'FloatField', 'FixedPointField',
           'ReferenceField', 'ComputedField', 'BooleanField',
           'CMFObjectField', 'ImageField', 'PhotoField',
           )


registerField(StringField,
              title='String',
              description='Used for storing simple strings')

registerField(FileField,
              title='File',
              description='Used for storing files')

registerField(TextField,
              title='Text',
              description=('Used for storing text which can be '
                           'used in transformations'))

registerField(DateTimeField,
              title='Date Time',
              description='Used for storing date/time')

registerField(LinesField,
              title='LinesField',
              description=('Used for storing text which can be '
                           'used in transformations'))

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
              description=('Used for storing references to '
                           'other Archetypes Objects'))

registerField(ComputedField,
              title='Computed',
              description=('Read-only field, which value is '
                           'computed from a python expression'))

registerField(BooleanField,
              title='Boolean',
              description='Used for storing boolean values')

registerField(CMFObjectField,
              title='CMF Object',
              description=('Used for storing value inside '
                           'a CMF Object, which can have workflow. '
                           'Can only be used for BaseFolder-based '
                           'content objects'))

registerField(ImageField,
              title='Image',
              description=('Used for storing images. '
                           'Images can then be retrieved in '
                           'different thumbnail sizes'))

registerField(PhotoField,
              title='Photo',
              description=('Used for storing images. '
                           'Based on CMFPhoto. ')
             )

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
registerPropertyType('storage', 'storage')
registerPropertyType('index', 'string')
