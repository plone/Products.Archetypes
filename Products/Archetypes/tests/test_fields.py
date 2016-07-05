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

import os
import PIL

from zope.annotation.interfaces import IAttributeAnnotatable
from zope.interface import implementer, alsoProvides
from zope.component import getSiteManager
from zope.publisher.browser import TestRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from plone.app.testing import PLONE_SITE_ID as portal_name

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.tests.utils import PACKAGE_HOME

from Products.Archetypes.atapi import Schema, DisplayList, IntDisplayList, BaseContentMixin, TextField
from Products.Archetypes.interfaces import IFieldDefaultProvider
from Products.Archetypes.interfaces.vocabulary import IVocabulary
from Products.Archetypes import Field as at_field
from Products import PortalTransforms
from OFS.Image import File, Image
from DateTime import DateTime


test_fields = [
    ('ObjectField', 'objectfield'),
    ('StringField', 'stringfield'),
    ('FileField', 'filefield'),
    ('TextField', 'textfield'),
    ('DateTimeField', 'datetimefield'),
    ('LinesField', 'linesfield'),
    ('IntegerField', 'integerfield'),
    ('FloatField', 'floatfield'),
    ('FloatField', 'floatfield2'),
    ('FixedPointField', 'fixedpointfield1'),
    ('FixedPointField', 'fixedpointfield2'),
    ('BooleanField', 'booleanfield'),
    ('ImageField', 'imagefield'),
]

field_instances = []
for type, name in test_fields:
    field_instances.append(getattr(at_field, type)(name))

txt_file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.rst'))
txt_content = txt_file.read()
img_file = open(os.path.join(PACKAGE_HOME, 'input', 'tool.gif'), 'rb')
img_content = img_file.read()
animated_gif_file = open(os.path.join(
    PACKAGE_HOME, 'input', 'animated.gif'), 'rb')
animated_gif_content = animated_gif_file.read()
pdf_file = open(os.path.join(PACKAGE_HOME, 'input', 'webdav.pdf'), 'rb')
pdf_content = pdf_file.read()

field_values = {
    'objectfield': 'objectfield',
    'stringfield': 'stringfield',
    'filefield_file': txt_file,
    'textfield': 'textfield',
    'datetimefield': '',
    'datetimefield_year': '2003',
    'datetimefield_month': '01',
    'datetimefield_day': '01',
    'datetimefield_hour': '03',
    'datetimefield_minute': '04',
    'linesfield': 'bla\nbla',
    'integerfield': '1',
    'floatfield': '1.5',
    'floatfield2': '1,2',
    'fixedpointfield1': '1.5',
    'fixedpointfield2': '1,5',
    'booleanfield': '1',
    'imagefield_file': img_file,
}

expected_values = {
    'objectfield': 'objectfield',
    'stringfield': 'stringfield',
    'filefield': txt_content,
    'textfield': 'textfield',
    'datetimefield': DateTime(2003, 01, 01, 03, 04),
    'linesfield': ('bla', 'bla'),
    'integerfield': 1,
    'floatfield': 1.5,
    'floatfield2': 1.2,
    'fixedpointfield1': '1.50',
    'fixedpointfield2': '1.50',
    'booleanfield': 1,
    'imagefield': '<img src="%s/dummy/imagefield" alt="Spam" title="Spam" height="16" width="16" />' % portal_name
}

empty_values = {
    'objectfield': None,
    'stringfield': '',
    'filefield': None,
    'textfield': '',
    'datetimefield': '2007-00-00',
    'linesfield': (),
    'integerfield': None,
    'floatfield': None,
    'floatfield2': None,
    'fixedpointfield1': None,
    'fixedpointfield2': None,
    'booleanfield': None,
}

schema = Schema(tuple(field_instances))
sampleDisplayList = DisplayList([('e1', 'e1'), ('element2', 'element2')])


@implementer(IVocabulary)
class sampleInterfaceVocabulary:

    def getDisplayList(self, instance):
        return sampleDisplayList


class Dummy(BaseContentMixin):

    def Title(self):
        # required for ImageField
        return 'Spam'

    def aMethod(self):
        return sampleDisplayList

    def default_val(self):
        return "World"


@implementer(IVocabularyFactory)
class DummyVocabulary(object):

    def __call__(self, context):
        return SimpleVocabulary.fromItems([("title1", "value1"), ("t2", "v2")])

DummyVocabFactory = DummyVocabulary()


@implementer(IVocabularyFactory)
class DummyIntVocabulary(object):

    def __call__(self, context):
        return SimpleVocabulary.fromItems([("title1", 1), ("t2", 2)])


DummyIntVocabFactory = DummyIntVocabulary()


FakeRequest = TestRequest
# class FakeRequest:
#
#    def __init__(self):
#        self.other = {}
#        self.form = {}


class ProcessingTest(ATSiteTestCase):

    def afterSetUp(self):
        self.setRoles(['Manager'])
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(Dummy, oid='dummy', context=self.portal,
                                       schema=schema)
        txt_file.seek(0)
        img_file.seek(0)
        pdf_file.seek(0)

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
            self.assertEqual(got, v, 'got: %r, expected: %r, field "%s"' %
                             (got, v, k))

    def test_processing_fieldset(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        dummy.processForm()
        for k, v in expected_values.items():
            got = dummy.getField(k).get(dummy)
            if isinstance(got, (File, Image)):
                got = str(got)
            self.assertEqual(got, v, 'got: %r, expected: %r, field "%s"' %
                             (got, v, k))

    def test_image_tag(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        dummy.processForm()

        image_field = dummy.getField('imagefield')
        self.assertEqual(image_field.tag(dummy),
                         '<img src="%s/dummy/imagefield" alt="Spam" title="Spam" height="16" width="16" />' % portal_name)
        self.assertEqual(image_field.tag(dummy, alt=''),
                         '<img src="%s/dummy/imagefield" alt="" title="Spam" height="16" width="16" />' % portal_name)
        self.assertEqual(image_field.tag(dummy, alt='', title=''),
                         '<img src="%s/dummy/imagefield" alt="" title="" height="16" width="16" />' % portal_name)

    def test_gif_format_preserved_when_scaling(self):
        dummy = self.makeDummy()

        image_field = dummy.getField('imagefield')

        scaled_image_file, img_format = image_field.scale(img_content, 5, 5)
        self.assertEqual("gif", img_format)

        image = PIL.Image.open(scaled_image_file)
        self.assertEqual("GIF", image.format)

    def test_dont_scale_animated_gif_when_original_is_smaller_than_scale_size(self):
        dummy = self.makeDummy()

        image_field = dummy.getField('imagefield')

        scaled_image_file, img_format = image_field.scale(
            animated_gif_content, 100, 100)
        self.assertEqual("gif", img_format)

        image = PIL.Image.open(scaled_image_file)
        self.assertEqual("GIF", image.format)
        image.seek(image.tell() + 1)

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
            size += s
            self.assertTrue(s, 'got: %s, field: %s' % (s, k))
        self.assertEqual(size, dummy.get_size())

    def test_validation(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.assertFalse(errors, errors)

    def test_validation_visible_fields(self):
        """ we assume that every field is visible """

        dummy = self.makeDummy()
        request = TestRequest()
        alsoProvides(request, IAttributeAnnotatable)
        my_values = field_values.copy()
        my_values['fixedpointfield2'] = 'an_error'
        request.form.update(my_values)
        request.form['fieldset'] = 'default'
        errors = {}
        dummy.validate(errors=errors, REQUEST=request)
        self.assertTrue(errors, errors)

    def test_validation_invisible_fields(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        my_values = field_values.copy()
        my_values['fixedpointfield2'] = 'an_error'
        request.form.update(my_values)
        request.form['fieldset'] = 'default'

        for field in dummy.Schema().filterFields(__name__='fixedpointfield2'):
            field.widget.visible['edit'] = 'invisible'
        errors = {}
        dummy.validate(errors=errors, REQUEST=request)
        self.assertFalse(errors, errors)

    def test_validation_hidden_fields(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        my_values = field_values.copy()
        my_values['fixedpointfield2'] = 'an_error'
        request.form.update(my_values)
        request.form['fieldset'] = 'default'
        for field in dummy.Schema().filterFields(__name__='fixedpointfield2'):
            field.widget.visible['edit'] = 'hidden'
        errors = {}
        dummy.validate(errors=errors, REQUEST=request)
        self.assertFalse(errors, errors)

    def test_double_validation(self):
        """ If a field already has an error and it is validated again,
        we cut the validation short and return the original error.

        Here we test that we do not lose the original error in the
        process.  We do that by adding the fieldsets twice in the
        request, which can happen if you have some whacky javascript
        that tries to clone too many inputs.
        """
        dummy = self.makeDummy()
        request = TestRequest()
        alsoProvides(request, IAttributeAnnotatable)
        my_values = field_values.copy()
        my_values['fixedpointfield2'] = 'an_error'
        request.form.update(my_values)
        request.form['fieldset'] = 'default'
        request.form['fieldsets'] = ['default', 'default']
        errors = {}
        dummy.validate(errors=errors, REQUEST=request)
        self.assertTrue(errors, errors)
        # The validation error looks a bit weird because of the
        # [[plone]] domain that is added by the translation testing
        # machinery.
        self.assertEqual(errors['fixedpointfield2'],
                         (u"[[plone][Validation failed(isDecimal): "
                          "'an_error' [[plone][is not a decimal number.]]]]"))

    def test_required(self):
        request = FakeRequest()
        request.form.update(empty_values)
        request.form['fieldset'] = 'default'
        self._test_required(request)

    def test_required_empty_request(self):
        request = FakeRequest()
        request.form = {}
        request.form['fieldset'] = 'default'
        self._test_required(request)

    def _test_required(self, request):
        dummy = self.makeDummy()
        f_names = []

        schema = dummy.Schema()
        for f in schema.fields():
            name = f.getName()
            f.required = 1
            f_names.append(name)
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.assertTrue(errors, "Errors dictionary is empty.")
        err_fields = errors.keys()
        failures = []
        for f_name in f_names:
            if f_name not in err_fields:
                failures.append(f_name)
        self.assertFalse(failures, "%s failed to report error." % failures)

    def test_static_vocabulary(self):
        dummy = self.makeDummy()
        field = dummy.Schema().fields()[0]

        # Default
        self.assertEqual(field.Vocabulary(), DisplayList())
        # DisplayList
        field.vocabulary = sampleDisplayList()
        self.assertEqual(field.Vocabulary(), sampleDisplayList)
        # List
        field.vocabulary = ['e1', 'element2']
        self.assertEqual(field.Vocabulary(), sampleDisplayList)
        # 2-Tuples
        field.vocabulary = [('e1', 'e1'), ('element2', 'element2')]
        self.assertEqual(field.Vocabulary(), sampleDisplayList)

    def test_dynamic_vocabulary(self):
        dummy = self.makeDummy()
        field = dummy.Schema().fields()[0]

        # Default
        self.assertEqual(field.Vocabulary(dummy), DisplayList())
        # Method
        field.vocabulary = 'aMethod'
        self.assertEqual(field.Vocabulary(dummy), sampleDisplayList)
        # DisplayList
        field.vocabulary = sampleDisplayList()
        self.assertEqual(field.Vocabulary(dummy), sampleDisplayList)
        # List
        field.vocabulary = ['e1', 'element2']
        self.assertEqual(field.Vocabulary(dummy), sampleDisplayList)
        # 2-Tuples
        field.vocabulary = [('e1', 'e1'), ('element2', 'element2')]
        self.assertEqual(field.Vocabulary(dummy), sampleDisplayList)
        # Interface
        field.vocabulary = sampleInterfaceVocabulary()
        self.assertEqual(field.Vocabulary(dummy), sampleDisplayList)

    def test_factory_vocabulary(self):
        dummy = self.makeDummy()
        field = dummy.Schema().fields()[0]

        # Default
        self.assertEqual(field.Vocabulary(dummy), DisplayList())

        expected = DisplayList([('value1', 'title1'), ('v2', 't2')])

        # # Vocabulary factory
        field.vocabulary = ()
        field.vocabulary_factory = 'archetypes.tests.dummyvocab'
        getSiteManager().registerUtility(component=DummyVocabFactory,
                                         name='archetypes.tests.dummyvocab')
        self.assertEqual(field.Vocabulary(dummy), expected)
        getSiteManager().unregisterUtility(
            component=DummyVocabFactory, name='archetypes.tests.dummyvocab')

    def test_factory_vocabulary_int(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        field = dummy.Schema().fields()[0]

        # Default
        self.assertEqual(field.Vocabulary(dummy), IntDisplayList())

        expected = IntDisplayList([(1, 'title1'), (2, 't2')])

        # # Vocabulary factory
        field.vocabulary = ()
        field.vocabulary_factory = 'archetypes.tests.dummyintvocab'
        getSiteManager().registerUtility(component=DummyIntVocabFactory,
                                         name='archetypes.tests.dummyintvocab')
        self.assertEqual(field.Vocabulary(), expected)
        getSiteManager().unregisterUtility(component=DummyIntVocabFactory,
                                           name='archetypes.tests.dummyintvocab')

    def test_allowable_content_types_ok(self):
        dummy = self.makeDummy()
        request = TestRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.assertFalse(errors, errors)

    def test_allowable_content_types_ofs_image_field(self):
        dummy = self.makeDummy()
        request = TestRequest()
        request.form.update(field_values)
        image = dummy.getField('imagefield')
        image.set(dummy, img_file)
        image = image.getAccessor(dummy)()
        # we need to set the filename to blank otherwise the mimetypes_registry
        # will pick up the correct mimetype from the filename and we need to
        # test a situation where the image field is of type Image from
        # Archetypes fields and the OFS image uploaded within it has no
        # filename set
        image.filename = ""
        image_file = image.data

        request.form.update({'imagefield_file': image_file})
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.assertFalse(errors, errors)

    def test_allowable_content_types_fail(self):
        dummy = self.makeDummy()
        request = TestRequest()
        request.form.update(field_values)
        request.form.update({'imagefield_file': pdf_file})
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        errors = {}
        dummy.validate(REQUEST=request, errors=errors)
        self.assertTrue(errors, errors)

    def test_defaults(self):
        dummy = self.makeDummy()
        field = dummy.Schema().fields()[0]

        # Default
        self.assertEqual(field.getDefault(dummy), None)

        # Value
        field.default = "Hello"
        self.assertEqual(field.getDefault(dummy), 'Hello')

        # Method
        field.default = None
        field.default_method = 'default_val'
        self.assertEqual(field.getDefault(dummy), 'World')

        # Adapter
        field.default_method = None

        @implementer(IFieldDefaultProvider)
        class DefaultFor(object):

            def __init__(self, context):
                self.context = context

            def __call__(self):
                return "Adapted"

        getSiteManager().registerAdapter(factory=DefaultFor,
                                         required=(Dummy,), name=field.__name__)
        self.assertEqual(field.getDefault(dummy), 'Adapted')
        getSiteManager().unregisterAdapter(factory=DefaultFor,
                                           required=(Dummy,), name=field.__name__)

    def test_encoding(self):
        # http://dev.plone.org/plone/ticket/7597
        dummy = self.makeDummy()
        field = dummy.Schema().fields()[3]  # textfield
        field.set(self.portal, 'some_text_with_weird_encoding', encoding='latin')
        encoding = field.getRaw(self.portal, raw=1).original_encoding
        self.assertEqual(encoding, 'latin')

    def test_mimetype(self):
        dummy = self.makeDummy()
        field = TextField('test', default_content_type='text/html')
        dummy.test = ''
        mimetype = field.getContentType(dummy)
        self.assertEqual('text/html', mimetype)


class DownloadTest(ATSiteTestCase):

    def afterSetUp(self):
        # Set up a content object with a field that has a word
        # document in it
        ATSiteTestCase.afterSetUp(self)
        self.dummy = mkDummyInContext(
            Dummy, oid='dummy', context=self.portal, schema=schema)
        self.field = self.dummy.getField('textfield')
        ptpath = PortalTransforms.__path__[0]
        self.wordfile = open('%s/tests/input/test.doc' % ptpath)
        self.field.getMutator(self.dummy)(self.wordfile.read())
        self.request = self.app.REQUEST
        self.response = self.request.response

    def test_download_from_textfield(self):
        # make sure field data doesn't get transformed when using the
        # download method
        value = self.field.download(self.dummy, no_output=True)
        self.assertFalse(isinstance(value, str))

    # XXX This test produces an UnicodeEncodeError in default Archetypes
    def DISABLED_test_download_filename_encoding(self):
        # When downloading, the filename is converted to ASCII:
        self.field.setFilename(self.dummy, '\xc3\xbcberzeugen')
        self.field.download(self.dummy, no_output=True)
        self.assertEqual(self.response.headers['content-disposition'],
                         'attachment; filename="uberzeugen"')
