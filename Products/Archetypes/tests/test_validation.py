################################################################################
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
################################################################################

from Products.Five.testbrowser import Browser

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase

from Products.validation import validation as validationService
from Products.validation.config import validation as validationConfig
from Products.validation.interfaces.IValidator import IValidator

from Products.ATContentTypes.content.document import ATDocumentSchema

class TestValidation(ATTestCase):
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
        self.failUnlessEqual(v('abcd'), 1)
        self.failUnlessEqual(v('a_123456'), 1)
        self.failIfEqual(v('123'), 1)
        self.failIfEqual(v('ab.c'), 1)
        self.failIfEqual(v('ab,c'),1 )
        self.failIfEqual(v('aaaaaaaab'), 1) # too long

class TestValidationViaBrowser(ATFunctionalSiteTestCase):
    """
    Test for http://dev.plone.org/plone/ticket/7580: 
    validators don't work on reference fields
    """

    def test_7580(self):
        """ """
        class DummyValidator:
            __implements__ = IValidator
        
            def __init__(self, name, title='', description=''):
                self.name = name
                self.title = title or name
                self.description = description

            def __call__(self, value, *args, **kw):
                return 'Value is always invalid!'

        validationConfig.register(DummyValidator('runDummy', title='', description=''))
        
        ## add dummy validator to ReferenceField
        ATDocumentSchema['relatedItems'].validators = ('runDummy',)
        ## validators from tuple must be converted to ValidationChain
        ## _validationLayer method will do it for us
        ATDocumentSchema['relatedItems']._validationLayer()
        
        ## we must login as Manager
        self.loginAsPortalOwner() 
        self.portal.acl_users.userFolderAddUser('root', 'secret', ['Manager'], []) 
        
        browser = Browser()
        browser.open(self.folder.absolute_url())
        browser.getLink('Log in').click() 
        browser.getControl('Login Name').value = 'root' 
        browser.getControl('Password').value = 'secret' 
        browser.getControl('Log in').click()
        
        browser.open(self.folder.absolute_url())

        ## try to add Page
        browser.getLink('Add new').click()
        browser.getControl('Page').click()
        browser.getControl('Add').click()

        browser.getControl('Title').value = 'TEST'
        browser.getControl('Save').click()
        
        ## Page can't be created because DummyValidator reejects value
        self.failUnless('Please correct the indicated errors.' in browser.contents)
        self.failUnless('Value is always invalid!' in browser.contents)     
        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestValidation))
    suite.addTest(makeSuite(TestValidationViaBrowser))
    return suite

