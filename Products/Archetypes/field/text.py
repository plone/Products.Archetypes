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
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storage import AttributeStorage
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.field.base import Field
from Products.Archetypes.field.base import ObjectField
from Products.Archetypes.field.file import FileField
from Products.Archetypes.exceptions import TextFieldException
# field specific imports
from types import UnicodeType, StringTypes, FileType
from Products.Archetypes import config
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import ITextField
from Products.Archetypes.interfaces.field import IStringField
from Products.Archetypes.interfaces.field import ILinesField
from Products.Archetypes.lib.baseunit import BaseUnit
from Products.Archetypes.widget import StringWidget
from Products.Archetypes.widget import LinesWidget



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
        value = unicode(value, encoding)
    return value

class StringField(ObjectField):
    """A field that stores strings"""
    __implements__ = IStringField
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

registerField(StringField,
              title='String',
              description='Used for storing simple strings')

class TextField(FileField):
    """Base Class for Field objects that rely on some type of
    transformation"""

    __implements__ = ITextField

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'text',
        'default' : '',
        'widget': StringWidget,
        'default_content_type' : 'text/plain',
        'default_output_type'  : 'text/plain',
        'allowable_content_types' : ('text/plain',),
        'primary' : False,
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

        if isinstance(value, basestring):
            return value

        raise TextFieldException(('Value is not File, String or '
                                  'BaseUnit on %s: %r' % (self.getName(),
                                                          type(value))))

    security.declarePrivate('getRaw')
    def getRaw(self, instance, raw=False, **kwargs):
        """
        If raw, return the base unit object, else return encoded raw data
        """
        value = self.get(instance, raw=True, **kwargs)
        if raw or not IBaseUnit.isImplementedBy(value):
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
            value = self.getStorage(instance).get(self.getName(), instance, **kwargs)
            if not IBaseUnit.isImplementedBy(value):
                return encode(value, instance, **kwargs)
        except AttributeError:
            # happens if new Atts are added and not yet stored in the instance
            if not kwargs.get('_initializing_', False):
                self.set(instance, self.getDefault(instance), _initializing_=True, **kwargs)
            return self.getDefault(instance)

        if raw:
            return value

        if mimetype is None:
            mimetype = self.default_output_type or 'text/plain'

        if not shasattr(value, 'transform'): # oldBaseUnits have no transform
            return str(value)
        data = value.transform(instance, mimetype)
        if not data and mimetype != 'text/plain':
            data = value.transform(instance, 'text/plain')
        return data or ''

    security.declarePrivate('getBaseUnit')
    def getBaseUnit(self, instance):
        """Return the value of the field wrapped in a base unit object
        """
        return self.get(instance, raw=True)

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
        if isinstance(value, unicode) and encoding is None:
            kwargs['encoding'] = 'UTF-8'

        # fix for external editor support
        # set mimetype to the last state if the mimetype in kwargs is None or 'None'
        mimetype = kwargs.get('mimetype', None)
        # NOTE: 'None' might be transmitted by external editor or the widgets
        # 'None' means None so no change to the mimetype
        if mimetype == 'None':
            kwargs['mimetype'] = self.getContentType(instance)
        # set filename to '' if not in kwargs
        kwargs['filename'] = kwargs.get('filename', '')

        if not IBaseUnit.isImplementedBy(value):
            value = BaseUnit(self.getName(), value, instance=instance,
                             **kwargs)

        ObjectField.set(self, instance, value, **kwargs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return len(self.getBaseUnit(instance))

registerField(TextField,
              title='Text',
              description=('Used for storing text which can be '
                           'used in transformations'))

class LinesField(ObjectField):
    """For creating lines objects"""
    __implements__ = ILinesField

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
        if isinstance(value, str):
            value =  value.split('\n')
        value = [decode(v.strip(), instance, **kwargs)
                 for v in value if v and v.strip()]
        value = tuple(value)
        ObjectField.set(self, instance, value, **kwargs)

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        value = ObjectField.get(self, instance, **kwargs) or ()
        data = [encode(v, instance, **kwargs) for v in value]
        return tuple(data)

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

registerPropertyType('multiValued', 'boolean', LinesField)

registerField(LinesField,
              title='LinesField',
              description=('Used for storing text which can be '
                           'used in transformations'))
