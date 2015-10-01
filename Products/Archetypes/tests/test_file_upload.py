##########################################################################
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
##########################################################################

# Load fixture
import os
import unittest

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from OFS.Image import File

from Products.Archetypes.atapi import MetadataStorage, BaseContent
from Products.Archetypes.tests.utils import PACKAGE_HOME


class FileLike:

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, chunk=None):
        if chunk == None:
            return self.data
        cur = self.pos
        next = cur + chunk
        self.pos = next
        return self.data[cur:next]

    def seek(self, pos, start=0):
        if start == 0:
            self.pos = pos
        if start == 1:
            self.pos += pos
        if start == 2:
            self.pos = len(self.data) - pos

    def tell(self):
        return self.pos


class FileFieldTest(ATSiteTestCase):

    def afterSetUp(self):
        from Products.Archetypes import Field
        from Products.MimetypesRegistry.MimeTypesRegistry import MimeTypesRegistry
        self.folder.mimetypes_registry = MimeTypesRegistry()
        self.folder._setOb('test_object_', BaseContent('test_object_'))
        self.instance = self.folder._getOb('test_object_')
        self.field = Field.FileField('file')
        self.factory = self.field.content_class

    def test_stringio_text(self):
        from cStringIO import StringIO
        f = StringIO('x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f)

    def test_stringio_binary(self):
        from cStringIO import StringIO
        f = StringIO('\x00' + 'x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f)

    def test_file_like_text(self):
        f = FileLike('x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f)

    def test_file_like_binary(self):
        f = FileLike('\x00' + 'x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f)

    def test_file_upload_text(self):
        from cgi import FieldStorage
        from ZPublisher.HTTPRequest import FileUpload
        from tempfile import TemporaryFile
        fp = TemporaryFile('w+b')
        fp.write('x' * (1 << 19))
        fp.seek(0)
        env = {'REQUEST_METHOD': 'PUT'}
        headers = {'content-type': 'text/plain',
                   'content-length': 1 << 19,
                   'content-disposition': 'attachment; filename=test.txt'}
        fs = FieldStorage(fp=fp, environ=env, headers=headers)
        f = FileUpload(fs)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertEqual(f, 'test.txt')

    def test_file_upload_binary(self):
        from cgi import FieldStorage
        from ZPublisher.HTTPRequest import FileUpload
        from tempfile import TemporaryFile
        fp = TemporaryFile('w+b')
        fp.write('\x00' + 'x' * (1 << 19))
        fp.seek(0)
        env = {'REQUEST_METHOD': 'PUT'}
        headers = {'content-type': 'text/plain',
                   'content-length': 1 << 19,
                   'content-disposition': 'attachment; filename=test.bin'}
        fs = FieldStorage(fp=fp, environ=env, headers=headers)
        f = FileUpload(fs)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertEqual(f, 'test.bin')

    def test_real_file_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f, f)

    def test_real_file_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f, f)

    def test_real_file_force_filename_detect_mime_pdf(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance,
                                            filename='file.pdf')
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/pdf')
        self.assertEqual(f, 'file.pdf')

    def test_real_file_force_filename_detect_mime_xml(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance,
                                            filename='file.xml')
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/xml')
        self.assertEqual(f, 'file.xml')

    def test_real_file_force_filename_detect_faq(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance,
                                            filename='file.faq')
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertEqual(f, 'file.faq')

    def test_real_file_force_mimetype(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd, instance=self.instance,
                                            mimetype='text/xml')
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/xml')
        self.assertFalse(f, f)

    def test_ofs_file_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        self.folder.f.content_type = 'text/plain'
        v, m, f = self.field._process_input(self.folder.f,
                                            instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        # Should retain content type.
        self.assertEqual(m, 'text/plain')
        self.assertEqual(f, self.folder.f.getId())

    def test_ofs_file_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f,
                                            instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertEqual(f, self.folder.f.getId())

    def test_pdata_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f.data,
                                            instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f)

    def test_pdata_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f.data,
                                            instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f)

    def test_string_text(self):
        f = 'x' * (1 << 19)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f)

    def test_string_binary(self):
        f = '\x00' + 'x' * (1 << 19)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f)

    def test_string_pdf(self):
        f = open(os.path.join(PACKAGE_HOME, 'input', 'webdav.pdf')).read()
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/pdf')
        self.assertFalse(f)

    def test_base_unit_text(self):
        from Products.Archetypes.BaseUnit import BaseUnit
        f = BaseUnit('f', 'x' * (1 << 19), instance=self.instance)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'text/plain')
        self.assertFalse(f)

    def test_base_unit_binary(self):
        from Products.Archetypes.BaseUnit import BaseUnit
        f = BaseUnit('f', '\x00' + 'x' * (1 << 19), instance=self.instance)
        v, m, f = self.field._process_input(f, instance=self.instance)
        self.assertTrue(isinstance(v, self.factory), (type(v), self.factory))
        self.assertEqual(m, 'application/octet-stream')
        self.assertFalse(f)

    def test_get(self):
        text = 'x' * (1 << 19)
        self.field.set(instance=self.instance, value=text)
        result = self.field.get(instance=self.instance)
        # For FileField, we should return a File for backwards
        # compatibility.
        self.assertTrue(isinstance(result, self.factory),
                        (type(result), self.factory))

    def test_get_metadata_storage(self):
        text = 'x' * (1 << 19)
        self.field.storage = MetadataStorage()
        self.field.set(instance=self.instance, value=text)
        result = self.field.get(instance=self.instance)
        # For FileField, we should return a File for backwards
        # compatibility.
        self.assertTrue(isinstance(result, self.factory),
                        (type(result), self.factory))

    def test_delete_file_via_set(self):
        sample = 'a sample text file to be deleted ............................'
        self.field.set(self.instance, sample)
        samplesize = self.field.get_size(self.instance)
        self.assertTrue(samplesize > 0)
        deletefile = 'DELETE_FILE'
        self.field.set(self.instance, deletefile)
        samplesize = self.field.get_size(self.instance)
        self.assertTrue(samplesize == 0)


class TextFieldTest(FileFieldTest):

    def afterSetUp(self):
        from Products.Archetypes import Field
        from Products.MimetypesRegistry.MimeTypesRegistry import MimeTypesRegistry
        from Products.PortalTransforms.TransformTool import TransformTool
        self.folder.mimetypes_registry = MimeTypesRegistry()
        self.folder.portal_transforms = TransformTool()
        self.folder._setOb('test_object_', BaseContent('test_object_'))
        self.instance = self.folder._getOb('test_object_')
        self.field = Field.TextField('file')
        self.factory = self.field.content_class

    def test_factory(self):
        from Products.Archetypes.BaseUnit import BaseUnit
        self.assertTrue(self.factory is BaseUnit)

    def test_field(self):
        from Products.Archetypes import Field
        self.assertTrue(isinstance(self.field, Field.TextField))

    def test_get(self):
        text = 'x' * (1 << 19)
        self.field.set(instance=self.instance, value=text)
        result = self.field.get(instance=self.instance)
        # For TextField, we should really return a string for
        # backwards compatibility.
        self.assertTrue(isinstance(result, str), type(result))

    def test_get_metadata_storage(self):
        text = 'x' * (1 << 19)
        self.field.storage = MetadataStorage()
        self.field.set(instance=self.instance, value=text)
        result = self.field.get(instance=self.instance)
        # For TextField, we should really return a string for
        # backwards compatibility.
        self.assertTrue(isinstance(result, str), type(result))
