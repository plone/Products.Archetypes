import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.Archetypes.tests.common import *

from Products.Archetypes.validation import validationService

class TestValidation(ArchetypesTestCase):
    def test_inNumericRange(self):
        v = validationService.validatorFor('inNumericRange')
        self.failUnlessEqual(v(10, 1, 20), 1)
        self.failUnlessEqual(v('10', 1, 20), 1)
        self.failIfEqual(v(0, 4, 5), 1)

    def test_isPrintable(self):
        v = validationService.validatorFor('isPrintable')
        self.failUnlessEqual(v('text'), 1)
        self.failIfEqual(v('\u203'), 1)
        self.failIfEqual(v(10), 1)

    def test_isSSN(self):
        v = validationService.validatorFor('isSSN')
        self.failUnlessEqual(v('111223333'), 1)
        self.failUnlessEqual(v('111-22-3333', ignore=r'-'), 1)

    def test_isUSPhoneNumber(self):
        v = validationService.validatorFor('isUSPhoneNumber')
        self.failUnlessEqual(v('(212) 555-1212',
                               ignore=r'[\s\(\)\-]'), 1)
        self.failUnlessEqual(v('2125551212',
                               ignore=r'[\s\(\)\-]'), 1)

        self.failUnlessEqual(v('(212) 555-1212'), 1)


    def test_isURL(self):
        v = validationService.validatorFor('isURL')
        self.failUnlessEqual(v('http://foo.bar:8080/manage'), 1)
        self.failIfEqual(v('http://\n'), 1)
        self.failIfEqual(v('../foo/bar'), 1)


    def test_isEmail(self):
        v = validationService.validatorFor('isEmail')
        self.failUnlessEqual(v('test@test.com'), 1)
        self.failIfEqual(v('@foo.bar'), 1)
        self.failIfEqual(v('me'), 1)

    def test_isUnixLikeName(self):
        v = validationService.validatorFor('isUnixLikeName')
        self.failUnless(v('abcd'))
        self.failUnless(v('a_123456'))
        self.failIf(v('123'))
        self.failIf(v('ab.c'))
        self.failIf(v('ab,c'))
        self.failIf(v('aaaaaaaab')) # too long


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestValidation))
    return suite

if __name__ == '__main__':
    framework()
