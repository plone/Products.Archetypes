import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import listTypes

from DateTime import DateTime
import unittest
from copy import deepcopy

schema = BaseSchema + Schema((
    TextField('atextfield',
              widget=StringWidget(description="Just a text field for the testing",
                                  label="A Text Field",
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
    ))


class Dummy(BaseContent):
    pass

def gen_dummy():
    Dummy.schema = deepcopy(schema)
    registerType(Dummy)
    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
   
class ClassGenTest( unittest.TestCase ):

    def setUp( self ):
        gen_dummy()
        self._dummy = Dummy(oid='dummy')
        self._dummy.initalizeArchetype()

    def test_methods(self):
        klass = self._dummy
        #setters
        self.failUnless(hasattr(klass, 'setAtextfield'))
        self.failUnless(hasattr(klass, 'setAlinesfield'))
        self.failUnless(hasattr(klass, 'setAdatefield'))
        self.failUnless(hasattr(klass, 'setAnobjectfield'))
        self.failUnless(hasattr(klass, 'setAfixedpointfield'))
        #getters
        self.failUnless(hasattr(klass, 'getAtextfield'))
        self.failUnless(hasattr(klass, 'getAlinesfield'))
        self.failUnless(hasattr(klass, 'getAdatefield'))
        self.failUnless(hasattr(klass, 'getAnobjectfield'))
        self.failUnless(hasattr(klass, 'getAfixedpointfield'))

    def test_textfield(self):
        klass = self._dummy
        klass.setAtextfield('Bla')
        self.failUnless(str(klass.getAtextfield()) == 'Bla')

    def test_linesfield(self):
        klass = self._dummy
        klass.setAlinesfield(['Bla', 'Ble', 'Bli'])
        self.failUnless(klass.getAlinesfield() == ['Bla', 'Ble', 'Bli'])

    def test_datefield(self):
        klass = self._dummy
        klass.setAdatefield('2002/01/01')
        self.failUnless(klass.getAdatefield() == DateTime('2002/01/01'))

    def test_objectfield(self):
        klass = self._dummy
        klass.setAnobjectfield('bla')
        self.failUnless(klass.getAnobjectfield() == 'bla')
                
    def test_fixedpointfield(self):
        klass = self._dummy
        klass.setAfixedpointfield('26.05')
        self.failUnless(klass.getAfixedpointfield() == '26.05')
                
    def tearDown( self ):
        del self._dummy
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ClassGenTest),
        ))

if __name__ == '__main__':
    unittest.main()
