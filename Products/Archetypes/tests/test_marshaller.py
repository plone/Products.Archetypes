"""
Unittests for marshaller

$Id: test_marshaller.py,v 1.4.4.1 2004/04/01 12:31:50 ajung Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *
from Products.Archetypes.public import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')

from Testing import ZopeTestCase
from Acquisition import aq_base
from Products.Archetypes.tests.test_sitepolicy import makeContent
import Products.Archetypes.config as config
from Products.Archetypes.examples.DDocument import DDocument

from ZPublisher.HTTPRequest import FileUpload
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.BaseRequest import RequestContainer
from Testing.makerequest import makerequest


import sys
from os import curdir
from os.path import join, abspath, dirname, split
import urllib

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

def aputrequest(file, content_type):
    resp = HTTPResponse(stdout=sys.stdout)
    environ = {}
    environ['SERVER_NAME']='foo'
    environ['SERVER_PORT']='80'
    environ['REQUEST_METHOD'] = 'PUT'
    environ['CONTENT_TYPE'] = content_type
    req = HTTPRequest(stdin=file, environ=environ, response=resp)
    return req

class MarshallerTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)

        user = self.getManagerUser()
        newSecurityManager(None, user)

    def test_textFieldObjectWordReplace(self):
        #test that uploading to an existing object works
        site = self.getPortal()
        obj1 = makeContent(site, portal_type='DDocument', id='obj1')

        wordFilePath = join(_prefix, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')
        data = wordFile.read()
        wordFile.seek(0)

        # put requests don't have the luxury of being able to specify a
        # content type
        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        word = site.obj1
        word.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(word.getContentType('body'), 'application/msword')
        self.assertEqual(word.getRawBody(), data)

    def test_textFieldObjectRSTreplace(self):
        ## And again with an RST
        site = self.getPortal()
        obj1 = makeContent(site, portal_type='DDocument', id='obj1')

        rstFilePath = join(_prefix, "input", "rest1.rst")
        rstFile = open(rstFilePath, 'r')
        data = rstFile.read()
        rstFile.seek(0)

        request = aputrequest(rstFile, 'text/x-rst')
        request.processInputs()
        rst = site.obj1
        rst.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(rst.getContentType('body'), 'text/x-rst')
        self.assertEqual(rst.getRawBody().strip(), data.strip())

    def test_fileFieldObjectWordReplace(self):
        #test that uploading to an existing object works
        site = self.getPortal()
        obj1 = makeContent(site, portal_type='SimpleFile', id='obj1')

        wordFilePath = join(_prefix, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')
        data = wordFile.read()
        wordFile.seek(0)

        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        word = site.obj1
        word.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(word.getContentType('body'), 'application/msword')
        self.assertEqual(str(word.getRawBody()), data)

    def setupCTR(self):
        #Modify the CTR to point to SimpleType
        site = self.getPortal()
        ctr = site.content_type_registry
        ctr.addPredicate('text', 'major_minor' )
        ctr.getPredicate('text' ).edit('text', '' )
        ctr.assignTypeName('text', 'DDocument')
        ctr.reorderPredicate('text', 0)

        ctr.addPredicate('msword', 'major_minor' )
        ctr.getPredicate('msword' ).edit( 'application', 'msword' )
        ctr.assignTypeName('msword', 'DDocument')
        ctr.reorderPredicate('msword', 1)

        return ctr

    def test_objectCreate(self):
        #create the correct object on upload
        #one day, but this will need a change to the factory
        site = self.getPortal()
        ctr = self.setupCTR()

        #now trigger the creation of a content type akin to DAV
        wordFilePath = join(_prefix, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')

        obj = site.PUT_factory('test', 'application/msword', wordFile)
        site._setObject('test', obj)

        obj = site['test']
        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        obj.PUT(request, request.RESPONSE)

        wordFile.seek(0)
        data = wordFile.read()

        word = site.test

        self.assertEqual(word.archetype_name, DDocument.archetype_name)
        self.assertEqual(str(word.getBody(raw=1)), data)
        self.assertEqual(word.getContentType('body'), 'application/msword')


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(MarshallerTests))
        return suite
