from copy import deepcopy
from cgi import escape
from cStringIO import StringIO
from logging import ERROR
from types import ClassType, FileType, StringType, UnicodeType

from zope.contenttype import guess_content_type
from zope.i18n import translate
from zope.i18nmessageid import Message
from zope import schema
from zope import component
from zope.interface import implements

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from DateTime import DateTime
from DateTime.DateTime import safelocaltime
from DateTime.interfaces import DateTimeError
from ExtensionClass import Base
from OFS.Image import File
from OFS.Image import Pdata
from OFS.Image import Image as BaseImage
from ZPublisher.HTTPRequest import FileUpload
from ZODB.POSException import ConflictError

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore import permissions

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.Layer import DefaultLayerContainer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.field import IStringField
from Products.Archetypes.interfaces.field import ITextField
from Products.Archetypes.interfaces.field import IDateTimeField
from Products.Archetypes.interfaces.field import ILinesField
from Products.Archetypes.interfaces.field import IIntegerField
from Products.Archetypes.interfaces.field import IFloatField
from Products.Archetypes.interfaces.field import IFileField
from Products.Archetypes.interfaces.field import IImageField
from Products.Archetypes.interfaces.field import IFixedPointField
from Products.Archetypes.interfaces.field import IReferenceField
from Products.Archetypes.interfaces.field import IComputedField
from Products.Archetypes.interfaces.field import IBooleanField
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces import IVocabulary
from Products.Archetypes.exceptions import ObjectFieldException
from Products.Archetypes.exceptions import TextFieldException
from Products.Archetypes.exceptions import FileFieldException
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.Widget import BooleanWidget
from Products.Archetypes.Widget import CalendarWidget
from Products.Archetypes.Widget import ComputedWidget
from Products.Archetypes.Widget import DecimalWidget
from Products.Archetypes.Widget import FileWidget
from Products.Archetypes.Widget import ImageWidget
from Products.Archetypes.Widget import IntegerWidget
from Products.Archetypes.Widget import LinesWidget
from Products.Archetypes.Widget import StringWidget
from Products.Archetypes.Widget import ReferenceWidget
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes.ReferenceEngine import Reference
from Products.Archetypes.log import log
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import Vocabulary
from Products.Archetypes.utils import className
from Products.Archetypes.utils import mapply
from Products.Archetypes.utils import shasattr
from Products.Archetypes.utils import contentDispositionHeader
from Products.Archetypes.mimetype_utils import getAllowedContentTypes as getAllowedContentTypesProperty
from Products.Archetypes import config
from Products.Archetypes.Storage import AttributeStorage
from Products.Archetypes.Storage import ObjectManagedStorage
from Products.Archetypes.Storage import ReadOnlyStorage
from Products.Archetypes.Registry import setSecurity
from Products.Archetypes.Registry import registerField
from Products.Archetypes.Registry import registerPropertyType

from Products.validation import ValidationChain
from Products.validation import UnknowValidatorError
from Products.validation import FalseValidatorError
from Products.validation.interfaces.IValidator import IValidator, IValidationChain

from Products.Archetypes.interfaces import IFieldDefaultProvider

from plone.uuid.interfaces import IUUID

# Import conditionally, so we don't introduce a hard depdendency
try:
    from plone.i18n.normalizer.interfaces import IUserPreferredFileNameNormalizer
    FILE_NORMALIZER = True
except ImportError:
    FILE_NORMALIZER = False

try:
    import PIL.Image
except ImportError:
    # no PIL, no scaled versions!
    log("Warning: no Python Imaging Libraries (PIL) found. "
        "Archetypes based ImageField's don't scale if neccessary.")
    HAS_PIL = False
    PIL_ALGO = None
else:
    HAS_PIL = True
    PIL_ALGO = PIL.Image.ANTIALIAS

STRING_TYPES = [StringType, UnicodeType]

_marker = []
CHUNK = 1 << 14

__docformat__ = 'reStructuredText'


def encode(value, instance, **kwargs):
    """ensure value is an encoded string"""
    if isinstance(value, unicode):
        encoding = kwargs.get('encoding')
        if encoding is None:
            try:
                encoding = instance.getCharset()
            except AttributeError:
                # that occurs during object initialization
                # (no acquisition wrapper)
                encoding = 'UTF8'
            if encoding is None:
                encoding = 'UTF8'
        value = value.encode(encoding)
    return value

def decode(value, instance, **kwargs):
    """ensure value is an unicode string"""
    if isinstance(value, str):
        encoding = kwargs.get('encoding')
        if encoding is None:
            try:
                encoding = instance.getCharset()
            except AttributeError:
                # that occurs during object initialization
                # (no acquisition wrapper)
                encoding = 'UTF8'
            if encoding is None:
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

    implements(IField, ILayerContainer)

    security = ClassSecurityInfo()

    _properties = {
        'old_field_name':None,
        'required' : False,
        'default' : None,
        'default_method' : None,
        'vocabulary' : (),
        'vocabulary_factory' : None,
        'enforceVocabulary' : False,
        'multiValued' : False,
        'searchable' : False,
        'isMetadata' : False,

        'accessor' : None,
        'edit_accessor' : None,
        'mutator' : None,
        'mode' : 'rw',

        'read_permission' : permissions.View,
        'write_permission' : permissions.ModifyPortalContent,

        'storage' : AttributeStorage(),

        'generateMode' : 'veVc',
        'force' : '',
        'type' : None,
        'widget': StringWidget,
        'validators' : (),
        'index' : None, # "KeywordIndex" or "<index_type>:schema"
        'index_method' : '_at_accessor', # method used for the index
                                         # _at_accessor an _at_edit_accessor
                                         # are the accessor and edit accessor
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
    def copy(self, name=None):
        """
        Return a copy of field instance, consisting of field name and
        properties dictionary. field name can be changed to given name.
        """
        cdict = dict(vars(self))
        cdict.pop('__name__')
        # Widget must be copied separatedly
        widget = cdict['widget']
        del cdict['widget']
        properties = deepcopy(cdict)
        properties['widget'] = widget.copy()
        name = name is not None and name or self.getName()
        return self.__class__(name, **properties)


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
        if shasattr(self, 'widget'):
            if type(self.widget) in (ClassType, type(Base)):
                self.widget = self.widget()
            self.widget.populateProps(self)

    def _validationLayer(self):
        """
        Resolve that each validator is in the service. If validator is
        not, log a warning.

        We could replace strings with class refs and keep things impl
        the ivalidator in the list.

        Note: this is not compat with aq_ things like scripts with __call__
        """
        chainname = 'Validator_%s' % self.getName()

        if isinstance(self.validators, dict):
            raise NotImplementedError, 'Please use the new syntax with validation chains'
        elif IValidationChain.providedBy(self.validators):
            validators = self.validators
        elif IValidator.providedBy(self.validators):
            validators = ValidationChain(chainname, validators=self.validators)
        elif isinstance(self.validators, (tuple, list, basestring)):
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
                if not validators[0][0].name.startswith('isEmpty'):
                    validators.insertSufficient('isEmptyNoError')
                    #validators.insertSufficient('isEmpty')
            else:
                validators.insertSufficient('isEmpty')

        self.validators = validators

    security.declarePublic('validate')
    def validate(self, value, instance, errors=None, **kwargs):
        """
        Validate passed-in value using all field validators.
        Return None if all validations pass; otherwise, return failed
        result returned by validator
        """
        if errors is None:
            errors = {}
        name = self.getName()
        if errors and errors.has_key(name):
            return True

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
            request = aq_get(instance, 'REQUEST')
            label = self.widget.Label(instance)
            name = self.getName()
            if isinstance(label, Message):
                label = translate(label, context=request)
            error = _(u'error_required',
                      default=u'${name} is required, please correct.',
                      mapping={'name': label})
            error = translate(error, context=request)
            errors[name] = error
            return error
        return None

    security.declarePrivate('validate_vocabulary')
    def validate_vocabulary(self, instance, value, errors):
        """Make sure value is inside the allowed values
        for a given vocabulary"""
        badvalues = []
        if value:
            # coerce value into a list called values
            values = value
            if isinstance(value, basestring):
                values = [value]
            elif isinstance(value, bool):
                values = [str(value)]
            elif not isinstance(value, (tuple, list)):
                raise TypeError("Field value type error: %s" % type(value))
            vocab = self.Vocabulary(instance)
            # filter empty
            values = [instance.unicodeEncode(v)
                      for v in values if v.strip()]
            # extract valid values from vocabulary
            valids = []
            for v in vocab:
                if isinstance(v, (tuple, list)):
                    v = v[0]
                if not isinstance(v, basestring):
                    v = str(v)
                valids.append(instance.unicodeEncode(v))
            # check field values
            badvalues = [val for val in values if not val in valids]

        error = None
        if badvalues:
            request = aq_get(instance, 'REQUEST')
            label = self.widget.Label(instance)
            if isinstance(label, Message):
                label = translate(label, context=request)
            if isinstance(val, Message):
                val = translate(val, context=request)
            error = _( u'error_vocabulary',
                default=u'Values ${val} are not allowed for vocabulary of element ${label}.',
                mapping={'val': unicode(badvalues), 'label': label})
            error = translate(error, context=request)
            errors[self.getName()] = error
        return error

    security.declarePublic('Vocabulary')
    def Vocabulary(self, content_instance=None):
        """
        Returns a DisplayList.

        Uses self.vocabulary as source.

        1) Static vocabulary

           - is already a DisplayList
           - is a list of 2-tuples with strings (see above)
           - is a list of strings (in this case a DisplayList
             with key=value will be created)

        2) Dynamic vocabulary:

           - precondition: a content_instance is given.

           - has to return a:

                * DisplayList or
                * list of strings or
                * list of 2-tuples with strings:
                    '[("key1","value 1"),("key 2","value 2"),]'

           - the output is postprocessed like a static vocabulary.

           - vocabulary is a string:
                if a method with the name of the string exists it will be called

           - vocabulary is a class implementing IVocabulary:
                the "getDisplayList" method of the class will be called.

        3) Zope 3 vocabulary factory vocabulary

            - precondition: a content_instance is given

            - self.vocabulary_factory is given

            - a named utility providing zope.schema.interfaces.IVocbularyFactory
              exists for the name self.vocabulary_factory.

        """
        value = self.vocabulary

        # Attempt to get the value from a a vocabulary factory if one was given
        # and no explicit vocabulary was set
        if not isinstance(value, DisplayList) and not value:
            factory_name = getattr(self, 'vocabulary_factory', None)
            if factory_name is not None:
                factory = component.getUtility(schema.interfaces.IVocabularyFactory, name=factory_name)
                factory_context = content_instance
                if factory_context is None:
                    factory_context = self
                value = DisplayList([(t.value, t.title or t.token) for t in factory(factory_context)])

        if not isinstance(value, DisplayList):

            if content_instance is not None and isinstance(value, basestring):
                # Dynamic vocabulary by method on class of content_instance
                method = getattr(content_instance, value, None)
                if method and callable(method):
                    args = []
                    kw = {'content_instance' : content_instance,
                          'field' : self}
                    value = mapply(method, *args, **kw)
            elif content_instance is not None and \
                 IVocabulary.providedBy(value):
                # Dynamic vocabulary provided by a class that
                # implements IVocabulary
                value = value.getDisplayList(content_instance)

            # Post process value into a DisplayList
            # Templates will use this interface
            sample = value[:1]
            if isinstance(sample, DisplayList):
                # Do nothing, the bomb is already set up
                pass
            elif isinstance(sample, (list, tuple)):
                # Assume we have ((value, display), ...)
                # and if not ('', '', '', ...)
                if sample and not isinstance((sample[0]), (list, tuple)):
                    # if not a 2-tuple
                    value = zip(value, value)
                value = DisplayList(value)
            elif len(sample) and isinstance(sample[0], basestring):
                value = DisplayList(zip(value, value))
            else:
                log('Unhandled type in Vocab: %s' % value)

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

        mode -- 'w' for write or 'r' for read
        instance -- The object being accessed according to the permission
        """
        if mode in ('w', 'write', 'edit', 'set'):
            perm = self.write_permission
        elif mode in ('r', 'read', 'view', 'get'):
            perm = self.read_permission
        else:
            return None
        return getSecurityManager().checkPermission( perm, instance )

    security.declarePublic('writeable')
    def writeable(self, instance, debug=False):
        if 'w' not in self.mode:
            if debug:
                log("Tried to update %s:%s but field is not writeable." % \
                    (instance.portal_type, self.getName()))
            return False

        method = self.getMutator(instance)
        if not method:
            if debug:
                log("No method %s on %s." % (self.mutator, instance))
            return False

        if not self.checkPermission('edit', instance):
            if debug:
                log("User %s tried to update %s:%s but "
                    "doesn't have enough permissions." %
                    (_getAuthenticatedUser(instance).getId(),
                     instance.portal_type, self.getName()))
            return False
        return True

    security.declarePublic('checkExternalEditor')
    def checkExternalEditor(self, instance):
        """ Checks if the user may edit this field and if
        external editor is enabled on this instance """

        pp = getToolByName(instance, 'portal_properties')
        sp = getattr(pp, 'site_properties', None)
        if sp is not None:
            if getattr(sp, 'ext_editor', None) \
                   and self.checkPermission(mode='edit', instance=instance):
                return True
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
    def getDefault(self, instance):
        """Return the default value to be used for initializing this
        field"""
        dm = self.default_method
        if dm:
            if isinstance(dm, basestring) and shasattr(instance, dm):
                method = getattr(instance, dm)
                return method()
            elif callable(dm):
                return dm()
            else:
                raise ValueError('%s.default_method is neither a method of %s'
                                 ' nor a callable' % (self.getName(),
                                                      instance.__class__))
        if not self.default:
            default_adapter = component.queryAdapter(instance, IFieldDefaultProvider, name=self.__name__)
            if default_adapter is not None:
                return default_adapter()

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

    security.declarePublic('getIndexAccessor')
    def getIndexAccessor(self, instance):
        """Return the index accessor, i.e. the getter for an indexable
        value."""
        return getattr(instance, self.getIndexAccessorName())

    security.declarePublic('getIndexAccessorName')
    def getIndexAccessorName(self):
        """Return the index accessor's name defined by the
        'index_method' field property."""
        if not hasattr(self, 'index_method'):
            return self.accessor
        elif self.index_method == '_at_accessor':
            return self.accessor
        elif self.index_method == '_at_edit_accessor':
            return self.edit_accessor or self.accessor

        # If index_method is not a string, we raise ValueError (this
        # is actually tested for in test_extensions_utils):
        elif not isinstance(self.index_method, (str, unicode)):
            raise ValueError("Bad index accessor value : %r"
                             % self.index_method)
        else:
            return self.index_method

    security.declarePrivate('toString')
    def toString(self):
        """Utility method for converting a Field to a string for the
        purpose of comparing fields.  This comparison is used for
        determining whether a schema has changed in the auto update
        function. Right now it's pretty crude."""
        # TODO fixme
        s = '%s(%s): {' % ( self.__class__.__name__, self.__name__ )
        sorted_keys = self._properties.keys()
        sorted_keys.sort()
        for k in sorted_keys:
            value = getattr( self, k, self._properties[k] )
            if k == 'widget':
                value = value.__class__.__name__
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            s = s + '%s:%s,' % (k, value )
        s = s + '}'
        return s

    security.declarePublic('isLanguageIndependent')
    def isLanguageIndependent(self, instance):
        """Get the language independed flag for i18n content
        """
        return self.languageIndependent

    security.declarePublic('getI18nDomain')
    def getI18nDomain(self):
        """ returns the internationalization domain for translation """
        pass

setSecurity(Field)

class ObjectField(Field):
    """Base Class for Field objects that fundamentaly deal with raw
    data. This layer implements the interface to IStorage and other
    Field Types should subclass this to delegate through the storage
    layer.
    """
    implements(IObjectField, ILayerContainer)

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'default_content_type' : 'application/octet-stream',
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
            # @@ and at every other possible occurence of an AttributeError?!!
            default = self.getDefault(instance)
            if not kwargs.get('_initializing_', False):
                self.set(instance, default, _initializing_=True, **kwargs)
            return default

    security.declarePrivate('getRaw')
    def getRaw(self, instance, **kwargs):
        if self.accessor is not None:
            accessor = self.getAccessor(instance)
        else:
            # self.accessor is None for fields wrapped by an I18NMixIn
            accessor = None
        kwargs.update({'field': self,
                       'encoding':kwargs.get('encoding', None),
                     })
        if accessor is None:
            args = [instance,]
            return mapply(self.get, *args, **kwargs)
        return mapply(accessor, **kwargs)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        kwargs['mimetype'] = kwargs.get('mimetype', getattr(self, 'default_content_type', 'application/octet-stream'))
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
        if not IStorage.providedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        # raw=1 is required for TextField
        value = self.get(instance, raw=True)
        self.unset(instance)
        self.storage = storage
        if shasattr(self.storage, 'initializeInstance'):
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

    security.declarePrivate('setContentType')
    def setContentType(self, instance, value):
        """Set mimetype in the base unit.
        """
        pass

    security.declarePublic('getContentType')
    def getContentType(self, instance, fromBaseUnit=True):
        """Return the mime type of object if known or can be guessed;
        otherwise, return default_content_type value or fallback to
        'application/octet-stream'.
        """
        value = ''
        if fromBaseUnit and shasattr(self, 'getBaseUnit'):
            bu = self.getBaseUnit(instance)
            if IBaseUnit.providedBy(bu):
                return str(bu.getContentType())
        raw = self.getRaw(instance)
        mimetype = getattr(aq_base(raw), 'mimetype', None)
        # some instances like OFS.Image have a getContentType method
        if mimetype is None:
            getCT = getattr(raw, 'getContentType', None)
            if callable(getCT):
                mimetype = getCT()
        # try to guess
        # guess_content_type can only handly ordinary strings, not unicode strings.
        # recode in utf-8 if the binary(!) content is handed over to it.
        if type(raw)==type(u'unicode'):
            raw=raw.encode('utf-8')
        if mimetype is None:
            mimetype, enc = guess_content_type('', str(raw), None)
        else:
            # mimetype may be an mimetype object
            mimetype = str(mimetype)
        # failed
        if mimetype is None:
            mimetype = getattr(self, 'default_content_type',
                               'application/octet-stream')
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

setSecurity(ObjectField)

class StringField(ObjectField):
    """A field that stores strings"""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'string',
        'default': '',
        'default_content_type' : 'text/plain',
        })

    implements(IStringField)

    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        if getattr(self, 'raw', False):
            return value
        return encode(value, instance, **kwargs)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        kwargs['field'] = self
        # Remove acquisition wrappers
        if not getattr(self, 'raw', False):
            value = decode(aq_base(value), instance, **kwargs)
        self.getStorage(instance).set(self.getName(), instance, value, **kwargs)

class FileField(ObjectField):
    """Something that may be a file, but is not an image and doesn't
    want text format conversion"""

    implements(IFileField, ILayerContainer)

    _properties = ObjectField._properties.copy()
    _properties.update({
        'type' : 'file',
        'default' : '',
        'primary' : False,
        'widget' : FileWidget,
        'content_class' : File,
        'default_content_type' : 'application/octet-stream',
        })

    security  = ClassSecurityInfo()

    security.declarePrivate('setContentType')
    def setContentType(self, instance, value):
        """Set mimetype in the base unit.
        """
        file = self.get(instance)
        try:
            # file might be None or an empty string
            setattr(file, 'content_type', value)
        except AttributeError:
            pass
        else:
            self.set(instance, file)

    security.declarePublic('getContentType')
    def getContentType(self, instance, fromBaseUnit=True):
        file = self.get(instance)
        return getattr(file, 'content_type', self.default_content_type)

    def _process_input(self, value, file=None, default=None, mimetype=None,
                       instance=None, filename='', **kwargs):
        if file is None:
            file = self._make_file(self.getName(), title='',
                                   file='', instance=instance)
        if IBaseUnit.providedBy(value):
            mimetype = value.getContentType() or mimetype
            filename = value.getFilename() or filename
            value = value.getRaw()
        elif isinstance(value, self.content_class):
            filename = getattr(value, 'filename', value.getId())
            mimetype = getattr(value, 'content_type', mimetype)
            return value, mimetype, filename
        elif isinstance(value, File):
            # In case someone changes the 'content_class'
            filename = getattr(value, 'filename', value.getId())
            mimetype = getattr(value, 'content_type', mimetype)
            value = value.data
        elif isinstance(value, FileUpload) or shasattr(value, 'filename'):
            filename = value.filename
        elif isinstance(value, FileType) or shasattr(value, 'name'):
            # In this case, give preference to a filename that has
            # been detected before. Usually happens when coming from PUT().
            if not filename:
                filename = value.name
                # Should we really special case here?
                for v in (filename, repr(value)):
                    # Windows unnamed temporary file has '<fdopen>' in
                    # repr() and full path in 'file.name'
                    if '<fdopen>' in v:
                        filename = ''
        elif isinstance(value, basestring):
            # Let it go, mimetypes_registry will be used below if available
            pass
        elif (isinstance(value, Pdata) or (shasattr(value, 'read') and
                                           shasattr(value, 'seek'))):
            # Can't get filename from those.
            pass
        elif value is None:
            # Special case for setDefault
            value = ''
        else:
            klass = getattr(value, '__class__', None)
            raise FileFieldException('Value is not File or String (%s - %s)' %
                                     (type(value), klass))
        filename = filename[max(filename.rfind('/'),
                                filename.rfind('\\'),
                                filename.rfind(':'),
                                )+1:]
        file.manage_upload(value)
        if mimetype is None or mimetype == 'text/x-unknown-content-type':
            body = file.data
            if not isinstance(body, basestring):
                body = body.data
            mtr = getToolByName(instance, 'mimetypes_registry', None)
            if mtr is not None:
                kw = {'mimetype':None,
                      'filename':filename}
                # this may split the encoded file inside a multibyte character
                try:
                    d, f, mimetype = mtr(body[:8096], **kw)
                except UnicodeDecodeError:
                    d, f, mimetype = mtr(len(body) < 8096 and body or '', **kw)
            else:
                mimetype = getattr(file, 'content_type', None)
                if mimetype is None:
                    mimetype, enc = guess_content_type(filename, body, mimetype)
        # mimetype, if coming from request can be like:
        # text/plain; charset='utf-8'
        mimetype = str(mimetype).split(';')[0].strip()
        setattr(file, 'content_type', mimetype)
        setattr(file, 'filename', filename)
        return file, mimetype, filename

    def _migrate_old(self, value, default=None, mimetype=None, **kwargs):
        filename = kwargs.get('filename', '')
        if isinstance(value, basestring):
            filename = kwargs.get('filename', '')
            if mimetype is None:
                mimetype, enc = guess_content_type(filename, value, mimetype)
            if not value:
                return default, mimetype, filename
            return value, mimetype, filename
        elif IBaseUnit.providedBy(value):
            return value.getRaw(), value.getContentType(), value.getFilename()

        value = aq_base(value)

        if isinstance(value, File):
            # OFS.Image.File based
            filename = getattr(value, 'filename', value.getId())
            mimetype = value.content_type
            data = value.data
            if len(data) == 0:
                return default, mimetype, filename
            else:
                return data, mimetype, filename

        return '', mimetype, filename

    def _make_file(self, id, title='', file='', instance=None):
        """File content factory"""
        return self.content_class(id, title, file)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs)
        if value and not isinstance(value, self.content_class):
            value = self._wrapValue(instance, value)
        if (shasattr(value, '__of__', acquire=True)
            and not kwargs.get('unwrapped', False)):
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
        if value == "DELETE_FILE":
            if shasattr(instance, '_FileField_types'):
                delattr(aq_base(instance), '_FileField_types')
            ObjectField.unset(self, instance, **kwargs)
            return

        if not kwargs.has_key('mimetype'):
            kwargs['mimetype'] = None

        kwargs['default'] = self.getDefault(instance)
        initializing = kwargs.get('_initializing_', False)

        if not initializing:
            file = self.get(instance, raw=True, unwrapped=True)
        else:
            file = None
        factory = self.content_class
        if not initializing and not isinstance(file, factory):
            # Convert to same type as factory
            # This is here mostly for backwards compatibility
            v, m, f = self._migrate_old(file, **kwargs)
            kwargs['mimetype'] = m
            kwargs['filename'] = f
            obj = self._wrapValue(instance, v, **kwargs)
            # Store so the object gets a _p_jar,
            # if we are using a persistent storage, that is.
            ObjectField.set(self, instance, obj, **kwargs)
            file = self.get(instance, raw=True, unwrapped=True)
            # Should be same as factory now, but if it isn't, that's
            # very likely a bug either in the storage implementation
            # or on the field implementation.

        value, mimetype, filename = self._process_input(value, file=file,
                                                        instance=instance,
                                                        **kwargs)

        kwargs['mimetype'] = mimetype
        kwargs['filename'] = filename

        # remove ugly hack
        if shasattr(instance, '_FileField_types'):
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
        obj = self._make_file(self.getName(), title='',
                              file=value, instance=instance)
        setattr(obj, 'filename', filename)
        if IBaseUnit.providedBy(obj):
            if mimetype:
                obj.setContentType(instance, mimetype)
        else:
            setattr(obj, 'content_type', mimetype)
        setattr(obj, 'content_type', mimetype)
        try:
            delattr(obj, 'title')
        except (KeyError, AttributeError):
            pass

        return obj

    security.declarePrivate('getBaseUnit')
    def getBaseUnit(self, instance, full=False):
        """Return the value of the field wrapped in a base unit object
        """
        filename = self.getFilename(instance, fromBaseUnit=False)
        if not filename:
            filename = '' # self.getName()
        mimetype = self.getContentType(instance, fromBaseUnit=False)
        value = self.getRaw(instance) or self.getDefault(instance)
        if isinstance(aq_base(value), File):
            value = value.data
            if full:
                # This will read the whole file in memory, which is
                # very expensive specially with big files over
                # ZEO. With small files is not that much of an issue.
                value = str(value)
            elif not isinstance(value, basestring):
                # It's a Pdata object, get only the first chunk, which
                # should be good enough for detecting the mimetype
                value = value.data
        bu = BaseUnit(filename, aq_base(value), instance,
                      filename=filename, mimetype=mimetype)
        return bu

    security.declarePrivate('getFilename')
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
        """Set file name in the base unit.
        """
        bu = self.getBaseUnit(instance, full=True)
        bu.setFilename(filename)
        self.set(instance, bu)

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = getattr(value, 'get_size', lambda: value and str(value))()
        return ObjectField.validate_required(self, instance, value, errors)

    security.declareProtected(permissions.View, 'download')
    def download(self, instance, REQUEST=None, RESPONSE=None, no_output=False):
        """Kicks download.

        Writes data including file name and content type to RESPONSE
        """
        file = self.get(instance, raw=True)
        if not REQUEST:
            REQUEST = aq_get(instance, 'REQUEST')
        if not RESPONSE:
            RESPONSE = REQUEST.RESPONSE
        filename = self.getFilename(instance)
        if filename is not None:
            if FILE_NORMALIZER:
                filename = IUserPreferredFileNameNormalizer(REQUEST).normalize(
                    unicode(filename, instance.getCharset()))
            else:
                filename = unicode(filename, instance.getCharset())
            header_value = contentDispositionHeader(
                disposition='attachment',
                filename=filename)
            RESPONSE.setHeader("Content-Disposition", header_value)
        if no_output:
            return file
        return file.index_html(REQUEST, RESPONSE)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        file = self.get(instance)
        if isinstance(file, self.content_class):
            return file.get_size()
        # Backwards compatibility
        return len(str(file))

    security.declarePublic('getIndexAccessor')
    def getIndexAccessor(self, instance):
        name = self.getIndexAccessorName()
        if name in (self.edit_accessor, self.accessor):
            return lambda: self.getIndexable(instance)
        else:
            return ObjectField.getIndexAccessor(self, instance)

    security.declarePrivate('getIndexable')
    def getIndexable(self, instance):
        # XXX Naive implementation that loads all data contents into
        # memory.  To have this not happening set your field to not
        # 'searchable' (the default) or define your own 'index_method'
        # property.
        orig_mt = self.getContentType(instance)

        # If there's no path to text/plain, don't do anything
        transforms = getToolByName(instance, 'portal_transforms')
        if transforms._findPath(orig_mt, 'text/plain') is None:
            return ''

        f = self.get(instance)

        datastream = ''
        try:
            datastream = transforms.convertTo(
                "text/plain",
                str(f),
                mimetype = orig_mt,
                filename = self.getFilename(instance, 0),
                )
        except (ConflictError, KeyboardInterrupt):
            raise
        except Exception, e:
            log("Error while trying to convert file contents to 'text/plain' "
                "in %r.getIndexable() of %r: %s" % (self, instance, e))

        value = str(datastream)
        return value

class TextField(FileField):
    """Base Class for Field objects that rely on some type of
    transformation"""

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'text',
        'default' : '',
        'widget': StringWidget,
        'default_content_type' : None,
        'default_output_type'  : 'text/plain',
        'allowable_content_types' : None,
        'primary' : False,
        'content_class': BaseUnit,
        })

    implements(ITextField)

    security  = ClassSecurityInfo()

    security.declarePublic('defaultView')
    def defaultView(self):
        return self.default_output_type

    security.declarePrivate('setContentType')
    def setContentType(self, instance, value):
        """Set mimetype in the base unit.
        """
        bu = self.get(instance, raw=True)
        if shasattr(bu, 'setContentType'):
            bu.setContentType(instance, value)
            self.set(instance, bu)
        else:
            log('Did not get a BaseUnit to set the content type',
                level=ERROR)

    getContentType = ObjectField.getContentType.im_func

    security.declarePublic('getAllowedContentTypes')
    def getAllowedContentTypes(self, instance):
        """ returns the list of allowed content types for this field.
            If the fields schema doesn't define any, the site's default
            values are returned.
        """
        act_attribute = getattr(self, 'allowable_content_types', None)
        if act_attribute is None:
            return getAllowedContentTypesProperty(instance)
        else:
            return act_attribute

    def _make_file(self, id, title='', file='', instance=None):
        return self.content_class(id, file=file, instance=instance)

    def _process_input(self, value, file=None, default=None,
                       mimetype=None, instance=None, **kwargs):
        if file is None:
            file = self._make_file(self.getName(), title='',
                                   file='', instance=instance)
        filename = kwargs.get('filename', None)
        body = None
        if IBaseUnit.providedBy(value):
            mimetype = value.getContentType() or mimetype
            filename = value.getFilename() or filename
            return value, mimetype, filename
        elif isinstance(value, self.content_class):
            filename = getattr(value, 'filename', value.getId())
            mimetype = getattr(value, 'content_type', mimetype)
            return value, mimetype, filename
        elif isinstance(value, File):
            # In case someone changes the 'content_class'
            filename = getattr(value, 'filename', value.getId())
            mimetype = getattr(value, 'content_type', mimetype)
            value = value.data
        elif isinstance(value, FileUpload) or shasattr(value, 'filename'):
            filename = value.filename
            # TODO Should be fixed eventually
            body = value.read(CHUNK)
            value.seek(0)
        elif isinstance(value, FileType) or shasattr(value, 'name'):
            # In this case, give preference to a filename that has
            # been detected before. Usually happens when coming from PUT().
            if not filename:
                filename = value.name
                # Should we really special case here?
                for v in (filename, repr(value)):
                    # Windows unnamed temporary file has '<fdopen>' in
                    # repr() and full path in 'file.name'
                    if '<fdopen>' in v:
                        filename = ''
            # TODO Should be fixed eventually
            body = value.read(CHUNK)
            value.seek(0)
        elif isinstance(value, basestring):
            # Let it go, mimetypes_registry will be used below if available
            pass
        elif isinstance(value, Pdata):
            pass
        elif shasattr(value, 'read') and shasattr(value, 'seek'):
            # Can't get filename from those.
            body = value.read(CHUNK)
            value.seek(0)
        elif value is None:
            # Special case for setDefault.
            value = ''
        else:
            klass = getattr(value, '__class__', None)
            raise TextFieldException('Value is not File or String (%s - %s)' %
                                     (type(value), klass))
        if isinstance(value, Pdata):
            # TODO Should be fixed eventually
            value = str(value)
        if isinstance(filename, basestring):
            filename = filename[max(filename.rfind('/'),
                                    filename.rfind('\\'),
                                    filename.rfind(':'),
                                    )+1:]

        if mimetype is None or mimetype == 'text/x-unknown-content-type':
            if body is None:
                body = value[:CHUNK]
            mtr = getToolByName(instance, 'mimetypes_registry', None)
            if mtr is not None:
                kw = {'mimetype':None,
                      'filename':filename}
                d, f, mimetype = mtr(body, **kw)
            else:
                mimetype, enc = guess_content_type(filename, body, mimetype)
        # mimetype, if coming from request can be like:
        # text/plain; charset='utf-8'
        mimetype = str(mimetype).split(';')[0]
        file.update(value, instance, mimetype=mimetype, **kwargs)
        file.setContentType(instance, mimetype)
        file.setFilename(filename)
        return file, str(file.getContentType()), file.getFilename()

    security.declarePrivate('getRaw')
    def getRaw(self, instance, raw=False, **kwargs):
        """
        If raw, return the base unit object, else return encoded raw data
        """
        value = self.get(instance, raw=True, **kwargs)
        if raw or not IBaseUnit.providedBy(value):
            return value
        kw = {'encoding':kwargs.get('encoding'),
              'instance':instance}
        args = []
        return mapply(value.getRaw, *args, **kw)

    security.declarePrivate('get')
    def get(self, instance, mimetype=None, raw=False, **kwargs):
        """ If raw, return the base unit object, else return value of
        object transformed into requested mime type.

        If no requested type, then return value in default type. If raw
        format is specified, try to transform data into the default output type
        or to plain text.
        If we are unable to transform data, return an empty string. """
        try:
            kwargs['field'] = self
            storage = self.getStorage(instance)
            value = storage.get(self.getName(), instance, **kwargs)
            if not IBaseUnit.providedBy(value):
                value = self._wrapValue(instance, value)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', False):
                self.set(instance, self.getDefault(instance),
                         _initializing_=True, **kwargs)
            value = self._wrapValue(instance, self.getDefault(instance))

        if raw:
            return value

        if mimetype is None:
            mimetype = self.default_output_type or 'text/plain'

        if not shasattr(value, 'transform'): # oldBaseUnits have no transform
            return str(value)
        data = value.transform(instance, mimetype,
                               encoding=kwargs.get('encoding',None))
        if not data and mimetype != 'text/plain':
            data = value.transform(instance, 'text/plain',
                                   encoding=kwargs.get('encoding',None))
        return data or ''

    security.declarePrivate('getBaseUnit')
    def getBaseUnit(self, instance, full=False):
        """Return the value of the field wrapped in a base unit object
        """
        return self.get(instance, raw=True)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return len(self.getBaseUnit(instance))

class DateTimeField(ObjectField):
    """A field that stores dates and times"""

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    implements(IDateTimeField)

    security  = ClassSecurityInfo()

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        try:
            DateTime(value)
        except DateTimeError:
            result = False
        else:
            # None is a valid DateTime input, but does not validate for
            # required.
            result = value is not None
        return ObjectField.validate_required(self, instance, result, errors)


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
                if value.timezoneNaive():
                    # Use local timezone for tz naive strings
                    # see http://dev.plone.org/plone/ticket/10141
                    zone = value.localZone(safelocaltime(value.timeTime()))
                    parts = value.parts()[:-1] + (zone,)
                    value = DateTime(*parts)
            except DateTimeError:
                value = None

        ObjectField.set(self, instance, value, **kwargs)

class LinesField(ObjectField):
    """For creating lines objects"""

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'lines',
        'default' : (),
        'widget' : LinesWidget,
        })

    implements(ILinesField)

    security  = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """
        If passed-in value is a string, split at line breaks and
        remove leading and trailing white space before storing in object
        with rest of properties.
        """
        __traceback_info__ = value, type(value)
        if isinstance(value, basestring):
            value =  value.split('\n')
        value = [decode(v.strip(), instance, **kwargs)
                 for v in value if v and v.strip()]
        if config.ZOPE_LINES_IS_TUPLE_TYPE:
            value = tuple(value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs) or ()
        data = [encode(v, instance, **kwargs) for v in value]
        if config.ZOPE_LINES_IS_TUPLE_TYPE:
            return tuple(data)
        else:
            return data

    security.declarePrivate('getRaw')
    def getRaw(self, instance, **kwargs):
        return self.get(instance, **kwargs)

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

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer',
        'size' : '10',
        'widget' : IntegerWidget,
        'default' : None,
        })

    implements(IIntegerField)

    security  = ClassSecurityInfo()

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        try:
            int(value)
        except (ValueError, TypeError):
            result = False
        else:
            result = True
        return ObjectField.validate_required(self, instance, result, errors)

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
        'default': None
        })

    implements(IFloatField)

    security  = ClassSecurityInfo()

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        try:
            float(value)
        except (ValueError, TypeError):
            result = False
        else:
            result = True
        return ObjectField.validate_required(self, instance, result, errors)


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
    """A field for storing numerical data with fixed points

    Test for fix for Plone issue #9414: '0' and '0.0' should count as values
    when validating required fields.  (A return value of None means validation
    passed.)

    >>> f = FixedPointField()
    >>> f.validate_required(None, '0', [])
    >>> f.validate_required(None, '0.0', [])
    """

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'fixedpoint',
        'precision' : 2,
        'default' : None,
        'widget' : DecimalWidget,
        'validators' : ('isDecimal'),
        })

    implements(IFixedPointField)

    security  = ClassSecurityInfo()

    def _to_tuple(self, instance, value):
        """Turn the value into a tuple that we will store.

        We will test some inputs.

        >>> f = FixedPointField()
        >>> instance = object()
        >>> f._to_tuple(instance, '0')
        (0, 0)
        >>> f._to_tuple(instance, '1.0')
        (1, 0)
        >>> f._to_tuple(instance, '-1.0')
        (-1, 0)
        >>> f._to_tuple(instance, '0.5')
        (0, 50)
        >>> f._to_tuple(instance, None)

        Negative numbers between -1 and -0 need to be handled
        differently as there is no difference between +0 and -0.

        >>> f._to_tuple(instance, '-0.5')
        (0, -50)

        Commas are accepted too:

        >>> f._to_tuple(instance, '1,23')
        (1, 23)

        You can also start with a dot or comma:

        >>> f._to_tuple(instance, '.23')
        (0, 23)
        >>> f._to_tuple(instance, ',23')
        (0, 23)
        >>> f._to_tuple(instance, '-.23')
        (0, -23)

        Now for some precision:

        >>> f._to_tuple(instance, '1,2345')
        (1, 23)
        >>> g = FixedPointField(precision=4)
        >>> g._to_tuple(instance, '1,2345')
        (1, 2345)
        >>> g._to_tuple(instance, '10')
        (10, 0)
        >>> g._to_tuple(instance, '9.0001')
        (9, 1)


        """
        if not value:
            value = self.getDefault(instance)
        if value is None:
            return value

        # XXX :-(
        # Decimal Point is very english. as a first hack
        # we should allow also the more contintental european comma.
        # The clean solution is to lookup:
        # * the locale settings of the zope-server, Plone, logged in user
        # * maybe the locale of the browser sending the value.
        # same should happen with the output.
        if isinstance(value, basestring):
            value = value.replace(',','.')

        value = value.split('.')
        __traceback_info__ = (self, value)
        if len(value) < 2:
            value = (int(value[0]), 0)
        else:
            fra = value[1][:self.precision]
            fra += '0' * (self.precision - len(fra))
            # Handle leading comma e.g. .36
            if value[0] == '' or value[0] == '-':
                value[0] += '0'
            front = int(value[0])
            fra = int(fra)
            # Handle values between -1 and 0.
            if front == 0 and value[0].startswith('-'):
                fra = -1 * fra
            value = (front, fra)

        return value

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        value = self._to_tuple(instance, value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        template = '%%s%%d.%%0%dd' % self.precision
        value = ObjectField.get(self, instance, **kwargs)
        __traceback_info__ = (template, value)
        if value is None:
            return self.getDefault(instance)
        if isinstance(value, basestring):
            value = self._to_tuple(instance, value)
        front, fra = value
        sign = ''
        # Numbers between -1 and 0 are store with a negative fraction.
        if fra < 0:
            sign = '-'
            fra = abs(fra)
        return template % (sign, front, fra)


class ReferenceField(ObjectField):
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
        'keepReferencesOnCopy' : False,
        'referencesSortable' : False,
        'callStorageOnSet': False,
        'index_method' : '_at_edit_accessor',
        })

    implements(IReferenceField)

    security  = ClassSecurityInfo()

    referencesSortable = False

    security.declarePrivate('get')
    def get(self, instance, aslist=False, **kwargs):
        """get() returns the list of objects referenced under the relationship
        """
        res = instance.getRefs(relationship=self.relationship)

        # singlevalued ref fields return only the object, not a list,
        # unless explicitely specified by the aslist option

        if not self.multiValued:
            if len(res) > 1:
                log("%s references for non multivalued field %s of %s" % (len(res),
                                                                          self.getName(),
                                                                          instance))
            if not aslist:
                if res:
                    res = res[0]
                else:
                    res = None

        if not self.referencesSortable or not hasattr( aq_base(instance), 'at_ordered_refs'):
            return res

        rd = {}
        [rd.__setitem__(IUUID(r, None), r) for r in res]

        refs = instance.at_ordered_refs
        order = refs.get(self.relationship)
        if order is None:
            return res
        return [rd[uid] for uid in order if uid in rd.keys()]

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """Mutator.

        ``value`` is a either a list of UIDs or one UID string, or a
        list of objects or one object to which I will add a reference
        to. None and [] are equal.

        >>> for node in range(3):
        ...     _ = self.folder.invokeFactory('Refnode', 'n%s' % node)

        Use set with a list of objects:

        >>> nodes = self.folder.n0, self.folder.n1, self.folder.n2
        >>> nodes[0].setLinks(nodes[1:])
        >>> nodes[0].getLinks()
        [<Refnode...>, <Refnode...>]

        Use it with None or () to delete references:

        >>> nodes[0].setLinks(None)
        >>> nodes[0].getLinks()
        []

        Use a list of UIDs to set:

        >>> nodes[0].setLinks([n.UID() for n in nodes[1:]])
        >>> nodes[0].getLinks()
        [<Refnode...>, <Refnode...>]
        >>> nodes[0].setLinks(())
        >>> nodes[0].getLinks()
        []

        Setting multiple values for a non multivalued field will fail:

        >>> nodes[1].setLink(nodes)
        Traceback (most recent call last):
        ...
        ValueError: Multiple values ...

        Keyword arguments may be passed directly to addReference(),
        thereby creating properties on the reference objects:

        >>> nodes[1].setLink(nodes[0].UID(), foo='bar', spam=1)
        >>> ref = nodes[1].getReferenceImpl()[0]
        >>> ref.foo, ref.spam
        ('bar', 1)

        Empty BTreeFolders work as values (#1212048):

        >>> _ = self.folder.invokeFactory('SimpleBTreeFolder', 'btf')
        >>> nodes[2].setLink(self.folder.btf)
        >>> nodes[2].getLink()
        <SimpleBTreeFolder...>
        """
        tool = getToolByName(instance, REFERENCE_CATALOG)
        targetUIDs = [ref.targetUID for ref in
                      tool.getReferences(instance, self.relationship)]

        if value is None:
            value = ()

        if not isinstance(value, (list, tuple)):
            value = value,
        elif not self.multiValued and len(value) > 1:
            raise ValueError, \
                  "Multiple values given for single valued field %r" % self

        #convert objects to uids if necessary
        uids = []
        for v in value:
            if isinstance(v, basestring):
                uids.append(v)
            else:
                uids.append(IUUID(v, None))

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

        if self.referencesSortable:
            if not hasattr( aq_base(instance), 'at_ordered_refs'):
                instance.at_ordered_refs = {}

            instance.at_ordered_refs[self.relationship] = tuple( filter(None, uids) )

        if self.callStorageOnSet:
            #if this option is set the reference fields's values get written
            #to the storage even if the reference field never use the storage
            #e.g. if i want to store the reference UIDs into an SQL field
            ObjectField.set(self, instance, self.getRaw(instance), **kwargs)

    security.declarePrivate('getRaw')
    def getRaw(self, instance, aslist=False, **kwargs):
        """Return the list of UIDs referenced under this fields
        relationship
        """
        rc = getToolByName(instance, REFERENCE_CATALOG)
        brains = rc(sourceUID=IUUID(instance, None),
                    relationship=self.relationship)
        res = [b.targetUID for b in brains]
        if not self.multiValued and not aslist:
            if res:
                res = res[0]
            else:
                res = None

        if not self.multiValued or not self.referencesSortable or not hasattr(aq_base(instance), 'at_ordered_refs'):
            return res

        refs = instance.at_ordered_refs
        order = refs.get(self.relationship)
        if order is None:
            return res
        return [r for r in order if r in res]


    security.declarePublic('Vocabulary')
    def Vocabulary(self, content_instance=None):
        """Use vocabulary property if it's been defined."""
        if self.vocabulary or getattr(self, 'vocabulary_factory', None):
            return ObjectField.Vocabulary(self, content_instance)
        else:
            return self._Vocabulary(content_instance).sortedByValue()

    def _brains_title_or_id(self, brain, instance):
        """ ensure the brain has a title or an id and return it as unicode"""
        title = None
        if shasattr(brain, 'getId'):
            title = brain.getId
        if shasattr(brain, 'Title') and brain.Title != '':
            title = brain.Title

        if title is not None and isinstance(title, basestring):
            return decode(title, instance)

        raise AttributeError, "Brain has no title or id"

    def _Vocabulary(self, content_instance):
        pairs = []
        pc = getToolByName(content_instance, 'portal_catalog')
        uc = getToolByName(content_instance, config.UID_CATALOG)
        purl = getToolByName(content_instance, 'portal_url')

        allowed_types = self.allowed_types
        allowed_types_method = getattr(self, 'allowed_types_method', None)
        if allowed_types_method:
            meth = getattr(content_instance,allowed_types_method)
            allowed_types = meth(self)

        skw = allowed_types and {'portal_type':allowed_types} or {}
        brains = uc.searchResults(skw)

        if self.vocabulary_custom_label is not None:
            label = lambda b:eval(self.vocabulary_custom_label, {'b': b})
        elif self.vocabulary_display_path_bound != -1 and len(brains) > self.vocabulary_display_path_bound:
            at = _(u'label_at', default=u'at')
            label = lambda b:u'%s %s %s' % (self._brains_title_or_id(b, content_instance),
                                             at, b.getPath())
        else:
            label = lambda b:self._brains_title_or_id(b, content_instance)

        # The UID catalog is the correct catalog to pull this
        # information from, however the workflow and perms are not accounted
        # for there. We thus check each object in the portal catalog
        # to ensure it validity for this user.
        portal_base = purl.getPortalPath()
        path_offset = len(portal_base) + 1

        abs_paths = {}
        abs_path = lambda b, p=portal_base: '%s/%s' % (p, b.getPath())
        [abs_paths.update({abs_path(b):b}) for b in brains]

        pc_brains = pc(path=abs_paths.keys(), **skw)

        for b in pc_brains:
            b_path = b.getPath()
            # translate abs path to rel path since uid_cat stores
            # paths relative now
            path = b_path[path_offset:]
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
            if abs_paths.has_key(b_path):
                uid = abs_paths[b_path].UID
                if uid is None:
                    # the brain doesn't have an uid because the catalog has a
                    # staled object. THAT IS BAD!
                    raise ReferenceException("Brain for the object at %s "\
                        "doesn't have an UID assigned with. Please update your"\
                        " reference catalog!" % b_path)
                pairs.append((uid, label(b)))

        if not self.required and not self.multiValued:
            no_reference = _(u'label_no_reference',
                             default=u'<no reference>')
            pairs.insert(0, ('', no_reference))

        __traceback_info__ = (content_instance, self.getName(), pairs)
        return DisplayList(pairs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 0


class ComputedField(Field):
    """A field that always returns a computed."""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'computed',
        'expression': None,
        'widget' : ComputedWidget,
        'mode' : 'r',
        'storage': ReadOnlyStorage(),
        })

    implements(IComputedField)

    security = ClassSecurityInfo()

    security.declarePrivate('set')
    def set(self, *ignored, **kwargs):
        pass

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        """Return the computed value."""
        return eval(self.expression, {'context': instance, 'here' : instance})

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data.

        Used for get_size in BaseObject.
        """
        return 0

class BooleanField(ObjectField):
    """A field that stores boolean values."""
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'vocabulary': (('True','Yes', 'yes'),('False','No', 'no')),
        'widget' : BooleanWidget,
        })

    implements(IBooleanField)

    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = super(BooleanField, self).get(instance, **kwargs)
        if value is None:
            return value
        return bool(value)

    security.declarePrivate('getRaw')
    def getRaw(self, instance, **kwargs):
        value = super(BooleanField, self).getRaw(instance, **kwargs)
        if value is None:
            return value
        return bool(value)

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """If value is not defined or equal to 0, set field to false;
        otherwise, set to true."""
        if not value or value == '0' or value == 'False':
            value = False
        else:
            value = True

        ObjectField.set(self, instance, value, **kwargs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return True

class CMFObjectField(ObjectField):
    """
    COMMENT TODO
    """
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'portal_type': 'File',
        'default': None,
        'default_mime_type': 'application/octet-stream',
        'widget' : FileWidget,
        'storage': ObjectManagedStorage(),
        'workflowable': True,
        })

    security  = ClassSecurityInfo()

    def _process_input(self, value, default=None, **kwargs):
        __traceback_info__ = (value, type(value))
        if not isinstance(value, basestring):
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
            if not shasattr(info, 'constructInstance'):
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
        return True

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

        the official API to get tag (in a pagetemplate) is
        obj.getField('image').tag(obj, scale='mini')
        ...

        sizes may be the name of a method in the instance or a callable which
        returns a dict.

        Don't remove scales once they exist! Instead of removing a scale
        from the list of sizes you should set the size to (0,0). Thus
        removeScales method is able to find the scales to delete the
        data.

        Scaling will only be available if PIL is installed!

        If 'DELETE_IMAGE' will be given as value, then all the images
        will be deleted (None is understood as no-op)
        """

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'original_size': None,
        'max_size': None,
        'sizes' : {'thumb':(80,80)},
        'swallowResizeExceptions' : False,
        'pil_quality' : 88,
        'pil_resize_algo' : PIL_ALGO,
        'default_content_type' : 'image/png',
        'allowable_content_types' : ('image/gif','image/jpeg','image/png'),
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        'content_class': Image,
        })

    implements(IImageField)

    security  = ClassSecurityInfo()

    default_view = "view"

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        # Do we have to delete the image?
        if value == "DELETE_IMAGE" or value is None:
            self.removeScales(instance, **kwargs)
            # unset main field too
            ObjectField.unset(self, instance, **kwargs)
            return

        if not value:
            return

        kwargs.setdefault('mimetype', None)
        default = self.getDefault(instance)
        value, mimetype, filename = self._process_input(value, default=default,
                                                        instance=instance, **kwargs)
        # value is an OFS.Image.File based instance
        # don't store empty images
        get_size = getattr(value, 'get_size', None)
        if get_size is not None and get_size() == 0:
            return

        kwargs['mimetype'] = mimetype
        kwargs['filename'] = filename

        try:
            data = self.rescaleOriginal(value, **kwargs)
        except (ConflictError, KeyboardInterrupt):
            raise
        except:
            if not self.swallowResizeExceptions:
                raise
            else:
                data = str(value.data)
        # TODO add self.ZCacheable_invalidate() later
        self.createOriginal(instance, data, **kwargs)
        self.createScales(instance, value=data)

    security.declareProtected(permissions.View, 'getAvailableSizes')
    def getAvailableSizes(self, instance):
        """Get sizes

        Supports:
            self.sizes as dict
            A method in instance called like sizes that returns dict
            A callable
        """
        sizes = self.sizes
        if isinstance(sizes, dict):
            return sizes
        elif isinstance(sizes, basestring):
            method = getattr(instance, sizes)
            data = method()
            return data
        elif callable(sizes):
            return sizes()
        elif sizes is None:
            return {}
        else:
            raise TypeError, 'Wrong self.sizes has wrong type: %s' % type(sizes)

    security.declareProtected(permissions.ModifyPortalContent, 'rescaleOriginal')
    def rescaleOriginal(self, value, **kwargs):
        """rescales the original image and sets the data

        for self.original_size or self.max_size

        value must be an OFS.Image.Image instance
        """
        data = str(value.data)
        if not HAS_PIL:
            return data

        mimetype = kwargs.get('mimetype', self.default_content_type)

        if self.original_size or self.max_size:
            if not value:
                return self.default
            w=h=0
            if self.max_size:
                if value.width > self.max_size[0] or \
                       value.height > self.max_size[1]:
                    factor = min(float(self.max_size[0])/float(value.width),
                                 float(self.max_size[1])/float(value.height))
                    w = int(factor*value.width)
                    h = int(factor*value.height)
            elif self.original_size:
                w,h = self.original_size
            if w and h:
                __traceback_info__ = (self, value, w, h)
                fvalue, format = self.scale(data, w, h)
                data = fvalue.read()
        else:
            data = str(value.data)

        return data

    security.declarePrivate('createOriginal')
    def createOriginal(self, instance, value, **kwargs):
        """create the original image (save it)
        """
        if value:
            image = self._wrapValue(instance, value, **kwargs)
        else:
            image = self.getDefault(instance)

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

    security.declareProtected(permissions.ModifyPortalContent, 'createScales')
    def createScales(self, instance, value=_marker):
        """creates the scales and save them
        """
        sizes = self.getAvailableSizes(instance)
        if not HAS_PIL or not sizes:
            return
        # get data from the original size if value is None
        if value is _marker:
            img = self.getRaw(instance)
            if not img:
                return
            data = str(img.data)
        else:
            data = value

        # empty string - stop rescaling because PIL fails on an empty string
        if not data:
            return

        filename = self.getFilename(instance)

        for n, size in sizes.items():
            if size == (0,0):
                continue
            w, h = size
            id = self.getName() + "_" + n
            __traceback_info__ = (self, instance, id, w, h)
            try:
                imgdata, format = self.scale(data, w, h)
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                if not self.swallowResizeExceptions:
                    raise
                else:
                    # scaling failed, don't create a scaled version
                    continue

            mimetype = 'image/%s' % format.lower()
            image = self._make_image(id, title=self.getName(), file=imgdata,
                                     content_type=mimetype, instance=instance)
            # nice filename: filename_sizename.ext
            #fname = "%s_%s%s" % (filename, n, ext)
            #image.filename = fname
            image.filename = filename
            try:
                delattr(image, 'title')
            except (KeyError, AttributeError):
                pass
            # manually use storage
            self.getStorage(instance).set(id, instance, image,
                                          mimetype=mimetype, filename=filename)

    def _make_image(self, id, title='', file='', content_type='', instance=None):
        """Image content factory"""
        return self.content_class(id, title, file, content_type)

    security.declarePrivate('scale')
    def scale(self, data, w, h, default_format = 'PNG'):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        size = int(w), int(h)

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        
        if image.format == 'GIF' and size[0] >= image.size[0] and size[1] >= image.size[1]:
            try:
                image.seek(image.tell() + 1)
                # original image is animated GIF and no bigger than the scale requested
                # don't attempt to scale as this will lose animation
                original_file.seek(0)
                return original_file, 'gif'
            except EOFError:
                # image is not animated
                image.seek(0)
        
        # consider image mode when scaling
        # source images can be mode '1','L,','P','RGB(A)'
        # convert to greyscale or RGBA before scaling
        # preserve palletted mode (but not pallette)
        # for palletted-only image formats, e.g. GIF
        # PNG compression is OK for RGBA thumbnails
        original_mode = image.mode
        img_format = image.format and image.format or default_format
        if original_mode == '1':
            image = image.convert('L')
        elif original_mode == 'P':
            image = image.convert('RGBA')
        image.thumbnail(size, self.pil_resize_algo)
        # decided to only preserve palletted mode
        # for GIF, could also use image.format in ('GIF','PNG')
        if original_mode == 'P' and img_format == 'GIF':
            image = image.convert('P')
        thumbnail_file = StringIO()
        # quality parameter doesn't affect lossless formats
        image.save(thumbnail_file, img_format, quality=self.pil_quality)
        thumbnail_file.seek(0)
        return thumbnail_file, img_format.lower()

    security.declareProtected(permissions.View, 'getSize')
    def getSize(self, instance, scale=None):
        """get size of scale or original
        """
        img = self.getScale(instance, scale=scale)
        if not img:
            return 0, 0
        return img.width, img.height

    security.declareProtected(permissions.View, 'getScale')
    def getScale(self, instance, scale=None, **kwargs):
        """Get scale by name or original
        """
        if scale is None:
            return self.get(instance, **kwargs)
        else:
            id = self.getScaleName(scale=scale)
            try:
                image = self.getStorage(instance).get(id, instance, **kwargs)
            except AttributeError:
                return ''
            image = self._wrapValue(instance, image, **kwargs)
            if shasattr(image, '__of__', acquire=True) and not kwargs.get('unwrapped', False):
                return image.__of__(instance)
            else:
                return image

    security.declareProtected(permissions.View, 'getScaleName')
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

        TODO: We should only return the size of the original image
        """
        sizes = self.getAvailableSizes(instance)
        original = self.get(instance)
        size = original and original.get_size() or 0

        if sizes:
            for name in sizes.keys():
                id = self.getScaleName(scale=name)
                try:
                    data = self.getStorage(instance).get(id, instance)
                except AttributeError:
                    pass
                else:
                    size+=data and data.get_size() or 0
        return size

    security.declareProtected(permissions.View, 'tag')
    def tag(self, instance, scale=None, height=None, width=None, alt=None,
            css_class=None, title=None, **kwargs):
        """Create a tag including scale
        """
        image = self.getScale(instance, scale=scale)
        if image:
            img_width, img_height = self.getSize(instance, scale=scale)
        else:
            img_height=0
            img_width=0

        if height is None:
            height=img_height
        if width is None:
            width=img_width

        url = instance.absolute_url()
        if scale:
            url+= '/' + self.getScaleName(scale)
        else:
            url+= '/' + self.getName()

        if alt is None:
            alt = instance.Title()
        if title is None:
            title = instance.Title()

        values = {'src' : url,
                  'alt' : escape(alt, quote=True),
                  'title' : escape(title, quote=True),
                  'height' : height,
                  'width' : width,
                 }

        result = '<img src="%(src)s" alt="%(alt)s" title="%(title)s" '\
                 'height="%(height)s" width="%(width)s"' % values

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key, value in kwargs.items():
            if value:
                result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result


__all__ = ('Field', 'ObjectField', 'StringField',
           'FileField', 'TextField', 'DateTimeField', 'LinesField',
           'IntegerField', 'FloatField', 'FixedPointField',
           'ReferenceField', 'ComputedField', 'BooleanField',
           'CMFObjectField', 'ImageField',
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
registerPropertyType('old_field_name', 'string')
