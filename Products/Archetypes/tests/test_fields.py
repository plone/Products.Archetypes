import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from os import curdir
from os.path import join, abspath, dirname, split

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.config import ZOPE_LINES_IS_TUPLE_TYPE
from Products.Archetypes import listTypes
from Products.Archetypes import Field
from Products.Archetypes.interfaces.vocabulary import IVocabulary
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.Field import ScalableImage, Image
from OFS.Image import File, Image
from DateTime import DateTime

fields = ['ObjectField', 'StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField', 'FixedPointField',
          'BooleanField', 'ImageField', 'PhotoField',
          # 'ReferenceField', 'ComputedField', 'CMFObjectField',
          ]

field_instances = [Field.FixedPointField('fixedpointfield2')]
for name in fields:
    field_instances.append(getattr(Field, name)(name.lower()))


txt_file = open(join(PACKAGE_HOME, 'input', 'rest1.rst'))
txt_content = txt_file.read()
img_file = open(join(PACKAGE_HOME, 'input', 'tool.gif'))
img_content = img_file.read()

field_values = {'objectfield':'objectfield',
                'stringfield':'stringfield',
                'filefield_file':txt_file,
                'textfield':'textfield',
                'datetimefield':'2003-01-01',
                'linesfield':'bla\nbla',
                'integerfield':'1',
                'floatfield':'1.5',
                'fixedpointfield':  '1.5',
                'fixedpointfield2': '1,5',
                'booleanfield':'1',
                'imagefield_file':img_file,
                'photofield_file':img_file}

expected_values = {'objectfield':'objectfield',
                   'stringfield':'stringfield',
                   'filefield':txt_content,
                   'textfield':'textfield',
                   'datetimefield':DateTime('2003-01-01'),
                   'linesfield':('bla', 'bla'),
                   'integerfield': 1,
                   'floatfield': 1.5,
                   'fixedpointfield':  '1.50',
                   'fixedpointfield2': '1.50',
                   'booleanfield': 1,
                   'imagefield':'<img src="portal/dummy/imagefield" alt="Spam" title="Spam" longdesc="" height="16" width="16" />', # this only works for Plone b/c of monkeypatch
                   'photofield':'<img src="portal/dummy/photofield/variant/original" alt="" title="" height="16" width="16" border="0" />'}

empty_values = {'objectfield':None,
                   'stringfield':'',
                   'filefield':None,
                   'textfield':'',
                   'datetimefield':None,
                   'linesfield':(),
                   'integerfield': None,
                   'floatfield': None,
                   'fixedpointfield': None,
                   'booleanfield': None,
                   #XXX'imagefield':"DELETE_IMAGE",
                   #XXX'photofield':"DELETE_IMAGE",
               }

if not ZOPE_LINES_IS_TUPLE_TYPE:
    expected_values['linesfield'] = list(expected_values['linesfield'])

schema = Schema(tuple(field_instances))
sampleDisplayList = DisplayList([('e1', 'e1'), ('element2', 'element2')])

class sampleInterfaceVocabulary:
    __implements__ = IVocabulary
    def getDisplayList(self, instance):
        return sampleDisplayList

class Dummy(BaseContentMixin):
    def Title(self):
        # required for ImageField
        return 'Spam'

    def aMethod(self):
        return sampleDisplayList


class FakeRequest:

    def __init__(self):
        self.other = {}
        self.form = {}


class ProcessingTest(ArcheSiteTestCase):

    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(Dummy, oid='dummy',
                                       context=self.portal,
                                       schema=schema)
        txt_file.seek(0)
        img_file.seek(0)

    def makeDummy(self):
        return self._dummy

    def test_processing(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        dummy.REQUEST = request
        dummy.processForm(data=1)
        for k, v in expected_values.items():
            got = dummy.getField(k).get(dummy)
            if isinstance(got, File):
                got = str(got)
            self.assertEquals(got, v, 'got: %r, expected: %r, field "%s"' %
                              (got, v, k))

##    def test_empty_processing(self):
##        dummy = self.makeDummy()
##        request = FakeRequest()
##        request.form.update(field_values)
##        dummy.REQUEST = request
##        dummy.processForm(data=1)
##
##        request.form.update(empty_values)
##        dummy.REQUEST = request
##        dummy.processForm(data=1)
##
##        for k, v in empty_values.items():
##            got = dummy.Schema()[k].get(dummy)
##            if isinstance(got, (File)) and not got.data:
##                got = None
##            if not got:
##                v = None
##            self.assertEquals(got, v, 'got: %r, expected: %r, field "%s"' %
##                              (got, v, k))


    def test_processing_fieldset(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        dummy.processForm()
        for k, v in expected_values.items():
            got = dummy.getField(k).get(dummy)
            if isinstance(got, (File, ScalableImage, Image)):
                got = str(got)
            self.assertEquals(got, v, 'got: %r, expected: %r, field "%s"' %
                              (got, v, k))

    def test_get_size(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        dummy.processForm()
        size = 0
        for k, v in expected_values.items():
            field = dummy.getField(k)
            s = field.get_size(dummy)
            size+=s
            self.failUnless(s, 'got: %s, field: %s' % (s, k))
        self.failUnlessEqual(size, dummy.get_size())

    def test_validation(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        errors = {}
        dummy.validate(errors=errors)
        self.failIf(errors, errors)

    def test_required(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form['fieldset'] = 'default'
        f_names = []

        schema = dummy.Schema()
        for f in schema.fields():
            name = f.getName()
            f.required = 1
            f_names.append(name)
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.failUnless(errors, "Errors dictionary is empty.")
        err_fields = errors.keys()
        failures = []
        for f_name in f_names:
            if f_name not in err_fields:
                failures.append(f_name)
        self.failIf(failures, "%s failed to report error." % failures)

    def test_static_vocabulary(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        field = dummy.Schema().fields()[0]

        # Default
        self.failUnlessEqual(field.Vocabulary(), DisplayList())
        # DisplayList
        field.vocabulary = sampleDisplayList()
        self.failUnlessEqual(field.Vocabulary(), sampleDisplayList)
        # List
        field.vocabulary = ['e1', 'element2']
        self.failUnlessEqual(field.Vocabulary(), sampleDisplayList)
        # 2-Tuples
        field.vocabulary = [('e1', 'e1'), ('element2', 'element2')]
        self.failUnlessEqual(field.Vocabulary(), sampleDisplayList)

    def test_dynamic_vocabulary(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        field = dummy.Schema().fields()[0]

        # Default
        self.failUnlessEqual(field.Vocabulary(dummy), DisplayList())
        # Method
        field.vocabulary = 'aMethod'
        self.failUnlessEqual(field.Vocabulary(dummy), sampleDisplayList)
        # DisplayList
        field.vocabulary = sampleDisplayList()
        self.failUnlessEqual(field.Vocabulary(dummy), sampleDisplayList)
        # List
        field.vocabulary = ['e1', 'element2']
        self.failUnlessEqual(field.Vocabulary(dummy), sampleDisplayList)
        # 2-Tuples
        field.vocabulary = [('e1', 'e1'), ('element2', 'element2')]
        self.failUnlessEqual(field.Vocabulary(dummy), sampleDisplayList)
        # Interface
        field.vocabulary = sampleInterfaceVocabulary()
        self.failUnlessEqual(field.Vocabulary(dummy), sampleDisplayList)

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


class FileFieldTest(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.field = Field.FileField('file')
        self.factory = self.field.content_class

    def test_stringio_text(self):
        from cStringIO import StringIO
        f = StringIO('x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.failIf(f)

    def test_stringio_binary(self):
        from cStringIO import StringIO
        f = StringIO('\x00' + 'x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.failIf(f)

    def test_file_like_text(self):
        f = FileLike('x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.failIf(f)

    def test_file_like_binary(self):
        f = FileLike('\x00' + 'x' * (1 << 19))
        f.seek(0)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.failIf(f)

    def test_file_upload_text(self):
        from cgi import FieldStorage
        from ZPublisher.HTTPRequest import FileUpload
        from tempfile import TemporaryFile
        fp = TemporaryFile('w+b')
        fp.write('x' * (1 << 19))
        fp.seek(0)
        env = {'REQUEST_METHOD':'PUT'}
        headers = {'content-type':'text/plain',
                   'content-length': 1 << 19,
                   'content-disposition':'attachment; filename=test.txt'}
        fs = FieldStorage(fp=fp, environ=env, headers=headers)
        f = FileUpload(fs)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.assertEquals(f, 'test.txt')

    def test_file_upload_binary(self):
        from cgi import FieldStorage
        from ZPublisher.HTTPRequest import FileUpload
        from tempfile import TemporaryFile
        fp = TemporaryFile('w+b')
        fp.write('\x00' + 'x' * (1 << 19))
        fp.seek(0)
        env = {'REQUEST_METHOD':'PUT'}
        headers = {'content-type':'text/plain',
                   'content-length': 1 << 19,
                   'content-disposition':'attachment; filename=test.bin'}
        fs = FieldStorage(fp=fp, environ=env, headers=headers)
        f = FileUpload(fs)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.assertEquals(f, 'test.bin')

    def test_real_file_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.assertEquals(f, fd.name)

    def test_real_file_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        v, m, f = self.field._process_input(fd)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.assertEquals(f, fd.name)

    def test_ofs_file_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        self.folder.f.content_type = 'text/plain'
        v, m, f = self.field._process_input(self.folder.f)
        self.failUnless(isinstance(v, self.factory))
        # Should retain content type.
        self.assertEquals(m, 'text/plain')
        self.assertEquals(f, self.folder.f.getId())

    def test_ofs_file_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.assertEquals(f, self.folder.f.getId())

    def test_pdata_text(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f.data)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.failIf(f)

    def test_pdata_binary(self):
        from tempfile import TemporaryFile
        fd = TemporaryFile('w+b')
        fd.write('\x00' + 'x' * (1 << 19))
        fd.seek(0)
        f = File('f', '', '')
        self.folder._setObject('f', f)
        self.folder.f.manage_upload(fd)
        v, m, f = self.field._process_input(self.folder.f.data)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.failIf(f)

    def test_string_text(self):
        f = 'x' * (1 << 19)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.failIf(f)

    def test_string_binary(self):
        f = '\x00' + 'x' * (1 << 19)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.failIf(f)

    def test_base_unit_text(self):
        from Products.Archetypes.BaseUnit import BaseUnit
        from Products.MimetypesRegistry.MimeTypesRegistry import MimeTypesRegistry
        self.folder.mimetypes_registry = MimeTypesRegistry()
        f = BaseUnit('f', 'x' * (1 << 19), instance=self.folder)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'text/plain')
        self.failIf(f)

    def test_base_unit_binary(self):
        from Products.Archetypes.BaseUnit import BaseUnit
        from Products.MimetypesRegistry.MimeTypesRegistry import MimeTypesRegistry
        self.folder.mimetypes_registry = MimeTypesRegistry()
        f = BaseUnit('f', '\x00' + 'x' * (1 << 19), instance=self.folder)
        v, m, f = self.field._process_input(f)
        self.failUnless(isinstance(v, self.factory))
        self.assertEquals(m, 'application/octet-stream')
        self.failIf(f)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ProcessingTest))
    suite.addTest(makeSuite(FileFieldTest))
    return suite

if __name__ == '__main__':
    framework()
