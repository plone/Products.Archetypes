import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *
from Products.Archetypes.public import *
from Products.Archetypes.config import *

from Products.validation import validation, interfaces

class MyValidator:
    __implements__ = (interfaces.ivalidator,)

    def __init__(self, name, fun):
        self.name = name
        self.fun = fun
    
    def __call__(self, value, instance, field, *args, **kwargs):
        return self.fun(value)

class FakeType(BaseObject):
    pass

class TestFieldValidation(ArchetypesTestCase):

    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        self.field = StringField('somefield')
        self.instance = FakeType('fake')

    def beforeTearDown(self):
        ArchetypesTestCase.beforeTearDown(self)

    def testRequiredPlusValidator(self):
        instance = FakeType('fake')
        validation.register(MyValidator('myv', lambda val:val))
        self.field.validators = ('myv',)
        errors = {}

        self.field.required = 0
        result = self.field.validate('horn', instance, errors,
                                     field=self.field)
        self.assertEquals(result, 'horn',
                          "The value of our validator was not returned.")

        errors.clear()
        self.field.required = 1
        result = self.field.validate('horn', instance, errors,
                                     field=self.field)
        self.assertEquals(result, 'horn',
                          "The value of our validator was not returned.")


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestFieldValidation))
        return suite
