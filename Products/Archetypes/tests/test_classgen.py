import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from copy import deepcopy

from DateTime import DateTime

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.tests.utils import gen_class
from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.MimetypesRegistry.MimeTypesTool import MimeTypesTool
from Products.PortalTransforms.TransformTool import TransformTool
from Products.CMFCore.DiscussionTool import DiscussionTool


default_text = """
Title
=====

Subtitle
--------
"""

schema = BaseSchema + Schema((
    TextField('atextfield',
              default_content_type='text/x-rst',
              default=default_text,
              widget=RichWidget(description="Just a text field for the testing",
                                  label="A Text Field",
                                  )),

    FileField('afilefield',
              primary=1,
              widget=RichWidget(description="Just a file field for the testing",
                                  label="A File Field",
                                  )),

    FileField('anotherfilefield', widget=FileWidget),
    
    LinesField('alinesfield', widget=LinesWidget),

    DateTimeField('adatefield',
                  widget=CalendarWidget(description="A date field",
                                        label="A Date Field")),

    ObjectField('anobjectfield',
                widget=StringWidget(description="An object field",
                                    label="An Object Field"),
                validators=('isURL',),
                ),

    FixedPointField('afixedpointfield',
                    widget=DecimalWidget(description="A fixed point field",
                                         label="A Fixed Point Field"),
                    ),
    StringField('awriteonlyfield', mode="w"),

    StringField('areadonlyfield', mode="r"),
    ))

class DummyDiscussionTool:
    def isDiscussionAllowedFor( self, content ):
        return False
    def overrideDiscussionFor(self, content, allowDiscussion):
        pass

class SiteProperties:
    default_charset = 'UTF-8'
    def getProperty(self, name, default=None):
        return getattr(self, name, default)

class PortalProperties:
    site_properties = SiteProperties()

class Dummy(BaseContent):
    portal_properties = PortalProperties()
    portal_discussion = DummyDiscussionTool()
    mimetypes_registry = MimeTypesTool()
    def __init__(self, oid='test', init_transforms=0, **kwargs):
        BaseContent.__init__(self, oid, **kwargs)
        self.portal_transforms = TransformTool()
        if init_transforms:
            from Products.PortalTransforms import transforms
            transforms.initialize(self.portal_transforms)

BaseUnit.portal_properties = PortalProperties()

def gen_dummy():
    gen_class(Dummy, schema)


class ClassGenTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(Dummy, oid='dummy', context=self.getPortal(),
                                      schema=schema)

    def test_methods(self):
        obj = self._dummy
        #setters
        self.failUnless(hasattr(obj, 'setAtextfield'))
        self.failUnless(hasattr(obj, 'setAfilefield'))
        self.failUnless(hasattr(obj, 'setAlinesfield'))
        self.failUnless(hasattr(obj, 'setAdatefield'))
        self.failUnless(hasattr(obj, 'setAnobjectfield'))
        self.failUnless(hasattr(obj, 'setAfixedpointfield'))
        self.failUnless(hasattr(obj, 'setAwriteonlyfield'))
        self.failUnless(not hasattr(obj, 'setAreadonlyfield'))
        #getters
        self.failUnless(hasattr(obj, 'getAtextfield'))
        self.failUnless(hasattr(obj, 'getAfilefield'))
        self.failUnless(hasattr(obj, 'getAlinesfield'))
        self.failUnless(hasattr(obj, 'getAdatefield'))
        self.failUnless(hasattr(obj, 'getAnobjectfield'))
        self.failUnless(hasattr(obj, 'getAfixedpointfield'))
        self.failUnless(not hasattr(obj, 'getAwriteonlyfield'))
        self.failUnless(hasattr(obj, 'getAreadonlyfield'))
        #raw getters
        self.failUnless(hasattr(obj, 'getRawAtextfield'))
        self.failUnless(hasattr(obj, 'getRawAfilefield'))
        self.failUnless(hasattr(obj, 'getRawAlinesfield'))
        self.failUnless(hasattr(obj, 'getRawAdatefield'))
        self.failUnless(hasattr(obj, 'getRawAnobjectfield'))
        self.failUnless(hasattr(obj, 'getRawAfixedpointfield'))
        self.failUnless(hasattr(obj, 'getRawAwriteonlyfield'))
        self.failUnless(not hasattr(obj, 'getRawAreadonlyfield'))

    def test_textfield(self):
        obj = self._dummy
        obj.setAtextfield('Bla', mimetype="text/plain")
        self.failUnlessEqual(str(obj.getAtextfield()), 'Bla')

    def test_filefield(self):
        obj = self._dummy
        obj.setAfilefield('Bla')
        self.failUnlessEqual(str(obj.getAfilefield()), 'Bla')

    def test_linesfield(self):
        obj = self._dummy
        obj.setAlinesfield(['Bla', 'Ble', 'Bli'])
        self.failUnlessEqual(obj.getAlinesfield(), ('Bla', 'Ble', 'Bli'))

    def test_datefield(self):
        obj = self._dummy
        obj.setAdatefield('2002/01/01')
        self.failUnlessEqual(obj.getAdatefield(), DateTime('2002/01/01'))

    def test_objectfield(self):
        obj = self._dummy
        obj.setAnobjectfield('bla')
        self.failUnlessEqual(obj.getAnobjectfield(), 'bla')

    def test_fixedpointfield(self):
        obj = self._dummy
        obj.setAfixedpointfield('26.05')
        self.failUnlessEqual(obj.getAfixedpointfield(), '26.05')

    def test_writeonlyfield(self):
        obj = self._dummy
        obj.setAwriteonlyfield('bla')
        self.failUnlessEqual(obj.getRawAwriteonlyfield(), 'bla')

    def test_getbaseunit(self):
        obj = self._dummy
        for field in obj.Schema().fields():
            if not hasattr(field,'getBaseUnit'):
                continue
            bu = field.getBaseUnit(obj)
            self.failUnless(IBaseUnit.isImplementedBy(bu),
               'Return value of %s.getBaseUnit() does not implement BaseUnit: %s' % (field.__class__, type(bu)))
            

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ClassGenTest))
    return suite

if __name__ == '__main__':
    framework()
