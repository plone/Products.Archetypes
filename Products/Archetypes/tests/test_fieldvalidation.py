import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *
from Products.Archetypes.public import *
from Products.Archetypes.config import *
from Products.Archetypes.BaseObject import BaseObject

from Products.validation import validation, interfaces

class MyValidator:
    __implements__ = (interfaces.ivalidator,)

    def __init__(self, name, fun):
        self.name = name
        self.fun = fun
    
    def __call__(self, value, instance, field, *args, **kwargs):
        return self.fun(value)

# never validates
validation.register(MyValidator('v1', lambda val:val))
# always validates
validation.register(MyValidator('v2', lambda val:1))
# never validates
validation.register(MyValidator('v3', lambda val:[]))

settings = [
    {'field': {}, # this is the dict of field properties
     'value': None,
     'assertion': lambda result:result is None, # result of field.validate()
     }, 

    {'field': {'required': 1},
     'value': None,
     'assertion': lambda result:result is not None},

    ]

for req in 0,1:
    for validator in (('v2', 'v1'), ('v1',)):
        settings.append(
            {'field': {'required': req, 'validators': validator},
             'value': 'bass',
             'assertion': lambda result:result == 'bass'}
            )

    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1},
         'value': 'cello',
         'assertion': lambda result:result is not None}
        )

    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1,
                   'vocabulary': ('frenchhorn', 'trombone', 'trumpet')},
         'value': 'trombone',
         'assertion': lambda result:result is None}
        )

    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1,
                   'vocabulary': ('frenchhorn', 'trombone', 'trumpet')},
         'value': 'tuba',
         'assertion': lambda result:result is not None}
        )

class FakeType(BaseObject):
    def unicodeEncode(self, v): return v # don't

class TestSettings(ArchetypesTestCase):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        self.instance = FakeType('fake')

    def testSettings(self):
        for setting in settings:
            field = Field('orchestra', **setting['field'])
            result = field.validate(setting['value'], self.instance, errors={})
            msg = 'Assertion failed for setting:\n%s.\nResult was "%s".' % \
                  (setting, result)
            
            self.assert_(setting['assertion'](result),
                         setting.get('failmsg', msg))

class TestValidation(ArchetypesTestCase):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        self.instance = FakeType('fake')

    def testIntegerZeroInvalid(self):
        # attach a validator that never validates, so any value must fail
        field = IntegerField('integer', validators=('v3',))

        self.assert_(field.validate(1, self.instance, errors={}) is not None)
        self.assert_(field.validate(0, self.instance, errors={}) is not None)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestSettings))
        suite.addTest(unittest.makeSuite(TestValidation))
        return suite
