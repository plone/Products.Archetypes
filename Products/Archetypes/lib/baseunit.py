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

import os.path

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.lib.logging import log, ERROR

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.Image import File
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.interfaces import IMimetypesRegistry, IMimetype
from Products.PortalTransforms.interfaces import idatastream
#from Products.MimetypesRegistry.mime_types import text_plain, \
#     application_octet_stream
from webdav.WriteLockInterface import WriteLockInterface

_marker = []

class BaseUnit(File):
    __implements__ = WriteLockInterface, IBaseUnit
    isUnit = 1

    security = ClassSecurityInfo()

    def __init__(self, name, file='', instance=None, **kw):
        self.id = self.__name__ = name
        self.update(file, instance, **kw)

    def __setstate__(self, dict):
        mimetype = dict.get('mimetype', None)
        if IMimetype.isImplementedBy(mimetype):
            dict['mimetype'] = str(mimetype)
            dict['binary'] = not not mimetype.binary
        assert(dict.has_key('mimetype'), 'no mimetype in setstate dict')
        File.__setstate__(self, dict)

    def update(self, data, instance, **kw):
        #Convert from str to unicode as needed
        mimetype = kw.get('mimetype', None)
        filename = kw.get('filename', None)
        encoding = kw.get('encoding', None)
        context  = kw.get('context', instance)

        adapter = getToolByName(context, 'mimetypes_registry')
        if not IMimetypesRegistry.isImplementedBy(adapter):
            raise RuntimeError('%s(%s) is not a valid mimetype registry' % \
                               (repr(adapter), repr(adapter.__class__)))
        data, filename, mimetype = adapter(data, **kw)

        assert mimetype
        self.mimetype = str(mimetype)
        self.binary = mimetype.binary
        if not self.isBinary():
            assert isinstance(data, unicode)
            if encoding is None:
                try:
                    encoding = adapter.guess_encoding(data)
                except UnboundLocalError:
                    # adapter is not defined, we are in object creation
                    import site
                    encoding = site.encoding
            self.original_encoding = encoding
        else:
            self.original_encoding = None
        self.raw  = data
        self.size = len(data)
        # taking care of stupid IE
        self.setFilename(filename)

    def transform(self, instance, mt):
        """Takes a mimetype so object.foo.transform('text/plain') should return
        a plain text version of the raw content

        return None if no data or if data is untranformable to desired output
        mime type
        """
        encoding = self.original_encoding
        orig = self.getRaw(encoding)
        if not orig:
            return None

        #on ZODB Transaction commit there is by specification
        #no acquisition context. If it is not present, take
        #the untransformed getRaw, this is necessary for
        #being used with APE
        # Also don't break if transform was applied with a stale instance
        # from the catalog while rebuilding the catalog
        if not instance or not hasattr(instance, 'aq_parent'):
            return orig

        transformer = getToolByName(instance, 'portal_transforms')
        data = transformer.convertTo(mt, orig, object=self, usedby=self.id,
                                     context=instance,
                                     mimetype=self.mimetype,
                                     filename=self.filename)

        if data:
            assert idatastream.isImplementedBy(data)
            _data = data.getData()
            instance.addSubObjects(data.getSubObjects())
            portal_encoding = self.portalEncoding(instance)
            encoding = data.getMetadata().get("encoding") or encoding \
                       or portal_encoding
            if portal_encoding != encoding:
                _data = unicode(_data, encoding).encode(portal_encoding)
            return _data

        # we have not been able to transform data
        # return the raw data if it's not binary data
        # FIXME: is this really the behaviour we want ?
        if not self.isBinary():
            portal_encoding = self.portalEncoding(instance)
            if portal_encoding != encoding:
                orig = self.getRaw(portal_encoding)
            return orig

        return None

    def __str__(self):
        return self.getRaw()

    __call__ = __str__

    def __len__(self):
        return self.get_size()

    def isBinary(self):
        """Return true if this contains a binary value, else false.
        """
        try:
            return self.binary
        except AttributeError:
            # XXX workaround for "[ 1040514 ] AttributeError on some types after
            # migration 1.2.4rc5->1.3.0"
            # Somehow and sometimes the binary attribute gets lost magically
            self.binary = not str(self.mimetype).startswith('text')
            log("BaseUnit: Failed to access attribute binary for mimetype %s. "
                "Setting binary to %s" % (self.mimetype, self.binary),
                level=ERROR)
            return self.binary

    # File handling
    def get_size(self):
        """Return the file size.
        """
        return self.size

    def getRaw(self, encoding=None, instance=None):
        """Return the file encoded raw value.
        """
        if self.isBinary():
            return self.raw
        # FIXME: backward compat, non binary data
        # should always be stored as unicode
        if not isinstance(self.raw, unicode):
            return self.raw
        if encoding is None:
            if instance is None:
                encoding ='UTF-8'
            else:
                # FIXME: fallback to portal encoding or original encoding ?
                encoding = self.portalEncoding(instance)
        return self.raw.encode(encoding)

    def portalEncoding(self, instance):
        """Return the default portal encoding, using an external python script.

        Look the archetypes skin directory for the default implementation.
        """
        try:
            return instance.getCharset()
        except AttributeError:
            # that occurs during object initialization
            # (no acquisition wrapper)
            return 'UTF8'

    def getContentType(self):
        """Return the file mimetype string.
        """
        return self.mimetype

    # Backward compatibility
    content_type = getContentType

    def setContentType(self, instance, value):
        """Set the file mimetype string.
        """
        mtr = getToolByName(instance, 'mimetypes_registry')
        if not IMimetypesRegistry.isImplementedBy(mtr):
            raise RuntimeError('%s(%s) is not a valid mimetype registry' % \
                               (repr(mtr), repr(mtr.__class__)))
        result = mtr.lookup(value)
        if not result:
            raise ValueError('Unknown mime type %s' % value)
        mimetype = result[0]
        self.mimetype = str(mimetype)
        self.binary = mimetype.binary

    def getFilename(self):
        """Return the file name.
        """
        return self.filename

    def setFilename(self, filename):
        """Set the file name.
        """
        if isinstance(filename, basestring):
            filename = os.path.basename(filename)
            self.filename = filename.split("\\")[-1]
        else:
            self.filename = filename

    ### index_html
    security.declareProtected(CMFCorePermissions.View, "index_html")
    def index_html(self, REQUEST, RESPONSE):
        """download method"""
        filename = self.getFilename()
        if filename:
            RESPONSE.setHeader('Content-Disposition',
                               'attachment; filename=%s' % filename)
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())

        RESPONSE.write(self.getRaw(encoding=self.original_encoding))
        return ''

    ### webDAV me this, webDAV me that
    security.declareProtected( CMFCorePermissions.ModifyPortalContent, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        mimetype=REQUEST.get_header('Content-Type', None)

        file = REQUEST.get('BODYFILE', _marker)
        if file is _marker:
            data = REQUEST.get('BODY', _marker)
            if data is _marker:
                raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
        else:
            data = file.read()
            file.seek(0)

        self.update(data, self.aq_parent, mimetype=mimetype)

        self.aq_parent.reindexObject()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self, REQUEST, RESPONSE):
        """Get the raw content for this unit.

        Also used for the WebDAV SRC.
        """
        RESPONSE.setHeader('Content-Type', self.getContentType())
        RESPONSE.setHeader('Content-Length', self.get_size())
        return self.getRaw(encoding=self.original_encoding)

InitializeClass(BaseUnit)

# XXX Backward-compatibility. Should eventually go away after 1.3-final.
newBaseUnit = BaseUnit
