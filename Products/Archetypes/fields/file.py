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
from types import StringType
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from ZPublisher.HTTPRequest import FileUpload
from OFS.Image import Pdata
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storages import AttributeStorage
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.fields.base import Field
from Products.Archetypes.fields.base import ObjectField

# field specific imports
from types import FileType
from OFS.Image import File
from OFS.content_types import guess_content_type
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import IFileField
from Products.Archetypes.widgets import FileWidget
from Products.Archetypes.storages import ObjectManagedStorage
from Products.Archetypes.lib.baseunit import BaseUnit
from Products.Archetypes.config import STRING_TYPES

__docformat__ = 'reStructuredText'

class FileField(ObjectField):
    """Something that may be a file, but is not an image and doesn't
    want text format conversion"""

    __implements__ = IFileField, ILayerContainer
    #XXX __implements__ = IFileField, IObjectField.__implements__

    _properties = ObjectField._properties.copy()
    _properties.update({
        'type' : 'file',
        'default' : '',
        'primary' : False,
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
          and shasattr(value, 'read') and shasattr(value, 'seek'):
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
            if isinstance(value, FileUpload) or shasattr(value, 'filename'):
                filename = value.filename
            if isinstance(value, FileType) or shasattr(value, 'name'):
                filename = value.name
            # Get only last part from a 'c:\\folder\\file.ext'
            filename = filename.split('\\')[-1]
            value.seek(0) # rewind
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
        if shasattr(value, '__of__', acquire=True) and not kwargs.get('unwrapped', False):
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
            if shasattr(instance, '_FileField_types'):
                delattr(aq_base(instance), '_FileField_types')
            ObjectField.unset(self, instance, **kwargs)
            return

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
            filename = ''

        mimetype = self.getContentType(instance, fromBaseUnit=False)
        value = self.getRaw(instance) or self.getDefault(instance)
        if isinstance(aq_base(value), File):
            value = str(aq_base(value).data)
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
        """Set file name in the base unit [PRIVATE]
        """
        bu = self.getBaseUnit(instance)
        bu.setFilename(filename)
        self.set(instance, bu)

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

registerField(FileField,
              title='File',
              description='Used for storing files')


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
        'workflowable': True,
        })

    security  = ClassSecurityInfo()

    def _process_input(self, value, default=None, **kwargs):
        __traceback_info__ = (value, type(value))
        if type(value) is not StringType:
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

registerField(CMFObjectField,
              title='CMF Object',
              description=('Used for storing value inside '
                           'a CMF Object, which can have workflow. '
                           'Can only be used for BaseFolder-based '
                           'content objects'))
