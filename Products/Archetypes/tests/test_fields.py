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
from Products.Archetypes.utils import DisplayList
from Products.Archetypes import Field
from Products.Archetypes.Field import ScalableImage, Image
from OFS.Image import File
from DateTime import DateTime

from test_classgen import Dummy as BaseDummy

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

fields = ['ObjectField', 'StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField', 'ImageField', 'PhotoField',
          # 'ReferenceField', 'ComputedField', 'CMFObjectField',
          ]

field_instances = []
for f in fields:
    field_instances.append(getattr(Field, f)(f.lower()))

txt_file = open(join(_prefix, 'input', 'rest1.rst'))
txt_content = txt_file.read()
img_file = open(join(_prefix, 'input', 'tool.gif'))
img_content = img_file.read()

field_values = {'objectfield':'objectfield',
                'stringfield':'stringfield',
                'filefield_file':txt_file,
                'textfield':'textfield',
                'datetimefield':'2003-01-01',
                'linesfield':'bla\nbla',
                'integerfield':'1',
                'floatfield':'1.5',
                'fixedpointfield': '1.5',
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
                   'fixedpointfield': '1.50',
                   'booleanfield': 1,
                   'imagefield':'<img src="imagefield" alt="Spam" title="Spam" longdesc="" height="16" width="16" />', # this only works for Plone b/c of monkeypatch
                   'photofield':'<img src="photofield/variant/original" alt="" title="" height="16" width="16" border="0" />'}

if not ZOPE_LINES_IS_TUPLE_TYPE:
    expected_values['linesfield'] = list(expected_values['linesfield'])


schema = Schema(tuple(field_instances))# + BaseDummy.schema.copy()

class Dummy(BaseDummy):
    schema = schema
    def Title(self): return 'Spam' # required for ImageField

del schema

class FakeRequest:

    def __init__(self):
        self.other = {}
        self.form = {}


class ProcessingTest(ArchetypesTestCase):

    def afterSetUp(self):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        txt_file.seek(0)
        img_file.seek(0)
        self.makeDummy()

    def makeDummy(self):
        self._dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        return self._dummy

    def test_processing(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        dummy.REQUEST = request
        dummy.processForm(data=1)
        for k, v in expected_values.items():
            got = dummy.Schema()[k].get(dummy)
            if isinstance(got, File):
                got = str(got)
            self.assertEquals(got, v, 'got: %r, expected: %r, field "%s"' %
                              (got, v, k))

    def test_processing_fieldset(self):
        dummy = self.makeDummy()
        request = FakeRequest()
        request.form.update(field_values)
        request.form['fieldset'] = 'default'
        dummy.REQUEST = request
        dummy.processForm()
        for k, v in expected_values.items():
            got = dummy.Schema()[k].get(dummy)
            if isinstance(got, (File, ScalableImage, Image)):
                got = str(got)
            self.assertEquals(got, v, 'got: %r, expected: %r, field "%s"' %
                              (got, v, k))

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


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ProcessingTest))
    return suite

if __name__ == '__main__':
    framework()
