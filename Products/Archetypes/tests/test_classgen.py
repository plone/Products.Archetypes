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
"""
"""

import unittest

from DateTime import DateTime
from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC, ACCESS_PRIVATE
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.tests.utils import gen_class
from Products.Archetypes import atapi
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.ClassGen import generateMethods
from Products.MimetypesRegistry.MimeTypesRegistry import MimeTypesRegistry
from Products.PortalTransforms.TransformTool import TransformTool


default_text = """
Title
=====

Subtitle
--------
"""

schema = atapi.BaseSchema + atapi.Schema((
    atapi.TextField('atextfield',
                    default_content_type='text/x-rst',
                    default=default_text,
                    widget=atapi.RichWidget(description="Just a text field for the testing",
                                            label="A Text Field",
                                            )),

    atapi.FileField('afilefield',
                    primary=1,
                    widget=atapi.RichWidget(description="Just a file field for the testing",
                                            label="A File Field",
                                            )),

    atapi.FileField('anotherfilefield', widget=atapi.FileWidget),

    atapi.LinesField('alinesfield', widget=atapi.LinesWidget),

    atapi.DateTimeField('adatefield',
                        widget=atapi.CalendarWidget(description="A date field",
                                                    label="A Date Field")),

    atapi.ObjectField('anobjectfield',
                      widget=atapi.StringWidget(description="An object field",
                                                label="An Object Field"),
                      validators=('isURL',),
                      ),

    atapi.FixedPointField('afixedpointfield',
                          widget=atapi.DecimalWidget(description="A fixed point field",
                                                     label="A Fixed Point Field"),
                          ),
    atapi.StringField('awriteonlyfield', mode="w"),

    atapi.StringField('areadonlyfield', mode="r"),
))


class DummyDiscussionTool:

    def isDiscussionAllowedFor(self, content):
        return False

    def overrideDiscussionFor(self, content, allowDiscussion):
        pass


class SiteProperties:
    default_charset = 'UTF-8'

    def getProperty(self, name, default=None):
        return getattr(self, name, default)

    def hasProperty(self, name):
        return hasattr(self, name)


class PortalProperties:
    site_properties = SiteProperties()


class Dummy(atapi.BaseContent):
    portal_properties = PortalProperties()
    portal_discussion = DummyDiscussionTool()
    mimetypes_registry = MimeTypesRegistry()

    def __init__(self, oid='test', init_transforms=0, **kwargs):
        atapi.BaseContent.__init__(self, oid, **kwargs)
        self.portal_transforms = TransformTool()
        if init_transforms:
            from Products.PortalTransforms import transforms
            transforms.initialize(self.portal_transforms)

atapi.BaseUnit.portal_properties = PortalProperties()


def gen_dummy():
    gen_class(Dummy, schema)


class ClassGenTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(Dummy, oid='dummy',
                                       context=self.portal,
                                       schema=schema)

    def test_methods(self):
        obj = self._dummy
        # setters
        self.assertTrue(hasattr(obj, 'setAtextfield'))
        self.assertTrue(hasattr(obj, 'setAfilefield'))
        self.assertTrue(hasattr(obj, 'setAlinesfield'))
        self.assertTrue(hasattr(obj, 'setAdatefield'))
        self.assertTrue(hasattr(obj, 'setAnobjectfield'))
        self.assertTrue(hasattr(obj, 'setAfixedpointfield'))
        self.assertTrue(hasattr(obj, 'setAwriteonlyfield'))
        self.assertTrue(not hasattr(obj, 'setAreadonlyfield'))
        # getters
        self.assertTrue(hasattr(obj, 'getAtextfield'))
        self.assertTrue(hasattr(obj, 'getAfilefield'))
        self.assertTrue(hasattr(obj, 'getAlinesfield'))
        self.assertTrue(hasattr(obj, 'getAdatefield'))
        self.assertTrue(hasattr(obj, 'getAnobjectfield'))
        self.assertTrue(hasattr(obj, 'getAfixedpointfield'))
        self.assertTrue(not hasattr(obj, 'getAwriteonlyfield'))
        self.assertTrue(hasattr(obj, 'getAreadonlyfield'))
        # raw getters
        self.assertTrue(hasattr(obj, 'getRawAtextfield'))
        self.assertTrue(hasattr(obj, 'getRawAfilefield'))
        self.assertTrue(hasattr(obj, 'getRawAlinesfield'))
        self.assertTrue(hasattr(obj, 'getRawAdatefield'))
        self.assertTrue(hasattr(obj, 'getRawAnobjectfield'))
        self.assertTrue(hasattr(obj, 'getRawAfixedpointfield'))
        self.assertTrue(hasattr(obj, 'getRawAwriteonlyfield'))
        self.assertTrue(not hasattr(obj, 'getRawAreadonlyfield'))

    def test_textfield(self):
        obj = self._dummy
        obj.setAtextfield('Bla', mimetype="text/plain")
        self.assertEqual(str(obj.getAtextfield()), 'Bla')

    def test_filefield(self):
        obj = self._dummy
        obj.setAfilefield('Bla')
        self.assertEqual(str(obj.getAfilefield()), 'Bla')

    def test_linesfield(self):
        obj = self._dummy
        obj.setAlinesfield(['Bla', 'Ble', 'Bli'])
        self.assertEqual(obj.getAlinesfield(), ('Bla', 'Ble', 'Bli'))

    def test_datefield(self):
        obj = self._dummy
        obj.setAdatefield('2002/01/01')
        self.assertEqual(obj.getAdatefield(), DateTime('2002/01/01'))

    def test_objectfield(self):
        obj = self._dummy
        obj.setAnobjectfield('bla')
        self.assertEqual(obj.getAnobjectfield(), 'bla')

    def test_fixedpointfield(self):
        obj = self._dummy
        obj.setAfixedpointfield('26.05')
        self.assertEqual(obj.getAfixedpointfield(), '26.05')

    def test_writeonlyfield(self):
        obj = self._dummy
        obj.setAwriteonlyfield('bla')
        self.assertEqual(obj.getRawAwriteonlyfield(), 'bla')

    def test1_getbaseunit(self):
        obj = self._dummy
        for field in obj.Schema().fields():
            if not hasattr(field, 'getBaseUnit'):
                continue
            bu = field.getBaseUnit(obj)
            self.assertTrue(IBaseUnit.providedBy(bu),
                            ('Return value of %s.getBaseUnit() does not '
                             'implement BaseUnit: %s' %
                             (field.__class__, type(bu))))


class SecDummy1:
    schema = {}
    sec = ClassSecurityInfo()
    sec.declareProtected('View', 'makeFoo')

    def makeFoo(self):
        return 'foo'


class SecDummy2:
    schema = {}

    def makeFoo(self):
        return 'foo'


class SecDummy3:
    schema = {}


class SecDummy4:
    schema = {}
    sec = ClassSecurityInfo()
    sec.declarePublic('makeFoo')

    def makeFoo(self):
        return 'foo'


class SecDummy5:
    schema = {}
    sec = ClassSecurityInfo()
    sec.declarePrivate('makeFoo')

    def makeFoo(self):
        return 'foo'

foo_field = atapi.StringField('foo',
                              accessor='makeFoo',
                              read_permission='Modify portal content',
                              write_permission='Modify portal content')


class ClassGenSecurityTest(unittest.TestCase):

    def test_security_dont_stomp_existing_decl_perm(self):
        self.assertFalse(hasattr(SecDummy1, '__ac_permissions__'))
        self.assertTrue(hasattr(SecDummy1, 'makeFoo'))
        existing_method = getattr(SecDummy1, 'makeFoo')
        generateMethods(SecDummy1, (foo_field,))
        self.assertTrue(hasattr(SecDummy1, '__ac_permissions__'))
        self.assertTrue(SecDummy1.makeFoo == existing_method)
        got = SecDummy1.__ac_permissions__
        expected = (('Modify portal content',
                     ('setFoo', 'getRawFoo')),
                    ('View', ('makeFoo',)),)
        self.assertEqual(got, expected)

    def test_security_dont_stomp_existing_decl_public(self):
        self.assertFalse(hasattr(SecDummy4, '__ac_permissions__'))
        self.assertFalse(hasattr(SecDummy4, 'makeFoo__roles__'))
        self.assertTrue(hasattr(SecDummy4, 'makeFoo'))
        existing_method = getattr(SecDummy4, 'makeFoo')
        generateMethods(SecDummy4, (foo_field,))
        self.assertTrue(hasattr(SecDummy4, '__ac_permissions__'))
        self.assertTrue(SecDummy4.makeFoo == existing_method)
        got = SecDummy4.__ac_permissions__
        expected = (('Modify portal content',
                     ('setFoo', 'getRawFoo')),)
        self.assertEqual(got, expected)
        self.assertTrue(hasattr(SecDummy4, 'makeFoo__roles__'))
        self.assertTrue(SecDummy4.makeFoo__roles__ == ACCESS_PUBLIC)

    def test_security_dont_stomp_existing_decl_private(self):
        self.assertFalse(hasattr(SecDummy5, '__ac_permissions__'))
        self.assertFalse(hasattr(SecDummy5, 'makeFoo__roles__'))
        self.assertTrue(hasattr(SecDummy5, 'makeFoo'))
        existing_method = getattr(SecDummy5, 'makeFoo')
        generateMethods(SecDummy5, (foo_field,))
        self.assertTrue(hasattr(SecDummy5, '__ac_permissions__'))
        self.assertTrue(SecDummy5.makeFoo == existing_method)
        got = SecDummy5.__ac_permissions__
        expected = (('Modify portal content',
                     ('setFoo', 'getRawFoo')),)
        self.assertEqual(got, expected)
        self.assertTrue(hasattr(SecDummy5, 'makeFoo__roles__'))
        self.assertTrue(SecDummy5.makeFoo__roles__ == ACCESS_PRIVATE)

    def test_security_protect_manual_method(self):
        self.assertFalse(hasattr(SecDummy2, '__ac_permissions__'))
        self.assertTrue(hasattr(SecDummy2, 'makeFoo'))
        existing_method = getattr(SecDummy2, 'makeFoo')
        generateMethods(SecDummy2, (foo_field,))
        self.assertTrue(hasattr(SecDummy2, '__ac_permissions__'))
        self.assertTrue(SecDummy2.makeFoo == existing_method)
        got = SecDummy2.__ac_permissions__
        expected = (('Modify portal content',
                     ('makeFoo', 'setFoo', 'getRawFoo')),)
        self.assertEqual(got, expected)

    def test_security_protect_generate_method(self):
        self.assertFalse(hasattr(SecDummy3, '__ac_permissions__'))
        self.assertFalse(hasattr(SecDummy3, 'makeFoo'))
        generateMethods(SecDummy3, (foo_field,))
        self.assertTrue(hasattr(SecDummy3, '__ac_permissions__'))
        self.assertTrue(hasattr(SecDummy3, 'makeFoo'))
        got = SecDummy3.__ac_permissions__
        expected = (('Modify portal content',
                     ('makeFoo', 'setFoo', 'getRawFoo')),)
        self.assertEqual(got, expected)
