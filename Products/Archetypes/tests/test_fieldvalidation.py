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

class FakeType(BaseObject):
    def unicodeEncode(self, v): return v # don't

settings = [
    {'field': {},
     'value': None,
     'assertion': lambda result:result is None},

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


class TestFieldValidation(ArchetypesTestCase):

    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self)
        self.instance = FakeType('fake')

    def beforeTearDown(self):
        ArchetypesTestCase.beforeTearDown(self)

    def testSettings(self):
        for setting in settings:
            errors = {}
            field = Field('orchestra', **setting['field'])
            result = field.validate(setting['value'], self.instance,
                                    errors, field=field)
            msg = 'Assertion failed for setting:\n%s.\nResult was "%s".' % \
                  (setting, result)
            
            self.assert_(setting['assertion'](result),
                         setting.get('failmsg', msg))

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
