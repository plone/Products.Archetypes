# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

# common imports
import sys
from types import ClassType
from copy import deepcopy
from cStringIO import StringIO

from ExtensionClass import Base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from ComputedAttribute import ComputedAttribute
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from OFS.content_types import guess_content_type
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.validation import ValidationChain
from Products.Archetypes.interfaces.validation import IValidator, IValidationChain
from Products.Archetypes.exceptions import UnknownValidatorError
from Products.Archetypes.exceptions import FalseValidatorError
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storages import AttributeStorage
from Products.Archetypes.lib.layer import DefaultLayerContainer
from Products.Archetypes.lib.translate import translate
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.lib.vocabulary import Vocabulary
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces.vocabulary import IVocabulary
from Products.Archetypes.widgets import StringWidget
from Products.Archetypes.registries import setSecurity
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.utils import className
from Products.Archetypes.lib.logging import log

__docformat__ = 'reStructuredText'

registerPropertyType('required', 'boolean')
registerPropertyType('default', 'string')
registerPropertyType('vocabulary', 'string')
registerPropertyType('enforceVocabulary', 'boolean')
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
        'required' : False,
        'default' : None,
        'default_method' : None,
        'vocabulary' : (),
        'enforceVocabulary' : False,
        'multiValued' : False,
        'searchable' : False,
        'isMetadata' : False,

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

        Note: XXX this is not compat with aq_ things like scripts with __call__
        """
        chainname = 'Validator_%s' % self.getName()

        if isinstance(self.validators, dict):
            raise NotImplementedError, 'Please use the new syntax with validation chains'
        elif IValidationChain.isImplementedBy(self.validators):
            validators = self.validators
        elif IValidator.isImplementedBy(self.validators):
            validators = ValidationChain(chainname, validators=self.validators)
        elif isinstance(self.validators, (tuple, list, str)):
            if len(self.validators):
                # got a non empty list or string - create a chain
                try:
                    validators = ValidationChain(chainname, validators=self.validators)
                except (UnknownValidatorError, FalseValidatorError), msg:
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
    def validate(self, value, instance, errors={}, **kwargs):
        """
        Validate passed-in value using all field validators.
        Return None if all validations pass; otherwise, return failed
        result returned by validator
        """
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
            label = self.widget.Label(instance)
            name = self.getName()
            error = translate(
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
            if isinstance(value, basestring):
                values = [value]
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
            for val in values:
                error = True
                for v in valids:
                    if val == v:
                        error = None
                        break

        if error:
            label = self.widget.Label(instance)
            errors[self.getName()] = error = translate(
                'archetypes', 'error_vocabulary',
                {'val': val, 'name': label}, instance,
                default = "Value %s is not allowed for vocabulary "
                "of element %s." % (val, label),
                )

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
        """

        value = self.vocabulary
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
                 IVocabulary.isImplementedBy(value):
                # Dynamic vocabulary provided by a class that
                # implements IVocabulary
                value = value.getDisplayList(content_instance)

            # Post process value into a DisplayList
            # Templates will use this interface
            sample = value[:1]
            if isinstance(sample, DisplayList):
                # Do nothing, the bomb is already set up
                pass
            elif isinstance(sample, (tuple, list)):
                # Assume we have ((value, display), ...)
                # and if not ('', '', '', ...)
                if sample and not isinstance(sample[0], (tuple, list)):
                    # if not a 2-tuple
                    value = zip(value, value)
                value = DisplayList(value)
            elif len(sample) and isinstance(sample[0], basestring):
                value = DisplayList(zip(value, value))
            else:
                log('Unhandled type in Vocab')
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
    #XXX
    def getDefault(self, instance):
        """Return the default value to be used for initializing this
        field"""
        dm = self.default_method
        if dm:
            if isinstance(dm, str) and shasattr(instance, dm):
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
            if not kwargs.get('_initializing_', False):
                self.set(instance, self.getDefault(instance), _initializing_=True, **kwargs)
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
        bu = self.getBaseUnit(instance)
        bu.setContentType(instance, value)
        self.set(instance, bu)

    security.declarePublic('getContentType')
    def getContentType(self, instance, fromBaseUnit=True):
        """Return the mime type of object if known or can be guessed;
        otherwise, return default_content_type value or fallback to
        'application/octet'.
        """
        value = ''
        if fromBaseUnit and shasattr(self, 'getBaseUnit'):
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
            # mimetype may be an mimetype object
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
