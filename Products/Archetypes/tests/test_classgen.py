import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except AttributeError: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import listTypes
from Products.Archetypes.BaseUnit import BaseUnit
from Products.PortalTransforms.MimeTypesTool import MimeTypesTool
from Products.PortalTransforms.TransformTool import TransformTool

from DateTime import DateTime
from copy import deepcopy

schema = BaseSchema + Schema((
    TextField('atextfield',
              widget=RichWidget(description="Just a text field for the testing",
                                  label="A Text Field",
                                  )),

    FileField('afilefield',
              widget=RichWidget(description="Just a file field for the testing",
                                  label="A File Field",
                                  )),

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


class SiteProperties:
    default_charset = 'UTF-8'
    def getProperty(self, name, default=None):
        return getattr(self, name, default)
    
class PortalProperties:
    site_properties = SiteProperties()

class Dummy(BaseContent):
    portal_properties = PortalProperties()
    mimetypes_registry = MimeTypesTool()
    
    def __init__(self, oid='test', init_transforms=0, **kwargs):
        BaseContent.__init__(self, oid, **kwargs)
        self.portal_transforms = TransformTool()
        if init_transforms:
            from Products.PortalTransforms import transforms
            transforms.initialize(self.portal_transforms)

BaseUnit.portal_properties = PortalProperties()

def gen_dummy():
    Dummy.schema = deepcopy(schema)
    registerType(Dummy)
    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)

class ClassGenTest( unittest.TestCase ):

    def setUp( self ):
        gen_dummy()
        self._dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

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
        self.failUnlessEqual(obj.getAlinesfield(), ['Bla', 'Ble', 'Bli'])

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
        
    def tearDown( self ):
        del self._dummy

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ClassGenTest),
        ))

if __name__ == '__main__':
    unittest.main()
