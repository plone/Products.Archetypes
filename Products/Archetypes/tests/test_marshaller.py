"""
Unittests for marshaller

$Id: test_marshaller.py,v 1.1.2.2 2004/02/02 22:26:52 dreamcatcher Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')

from Testing import ZopeTestCase
from Acquisition import aq_base
from Products.Archetypes.tests.test_sitepolicy import makeContent
import Products.Archetypes.config as config
from Products.Archetypes.examples.DDocument import DDocument

from ZPublisher.HTTPRequest import FileUpload
from Testing.makerequest import makerequest

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


def putfile(file, mime_type):
    class fooFile:
        def __init__(self, file):
            self.headers  = {'content-type' : mime_type}
            self.filename = file.name
            self.file = file
    return FileUpload(fooFile(file))


class MarshallerTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)

        user = self.getManagerUser()
        newSecurityManager(None, user)

    def test_objectReplace(self):
        #test that uploading to an existing object works
        site = self.getPortal()
        obj1 = makeContent(site, portal_type='DDocument', id='obj1')

        wordFilePath = join(_prefix, "input", "pdb.doc")
        wordFile = open(wordFilePath, 'r')
        data = wordFile.read()
        wordFile.seek(0)


        rc = makerequest(site)
        request = rc.REQUEST
        request.processInputs()
        request.form['BODYFILE'] = putfile(wordFile, 'application/msword')
        word = site.obj1
        word.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        assert word.getContentType('body') == 'application/msword'
        assert word.getRawBody() == data


    def test_rstreplace(self):
        ## And again with an RST
        site = self.getPortal()
        obj1 = makeContent(site, portal_type='DDocument', id='obj1')

        rstFilePath = join(_prefix, "input", "rest1.rst")
        rstFile = open(rstFilePath, 'r')
        data = rstFile.read()
        rstFile.seek(0)

        rc = makerequest(site)
        request = rc.REQUEST
        request.form['BODYFILE'] = putfile(rstFile, 'text/x-rst')
        rst = site.obj1
        rst.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        assert rst.getContentType('body') == 'text/x-rst'
        assert rst.getRawBody().strip() == data.strip()


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
        wordFilePath = join(_prefix, "input", "pdb.doc")
        wordFile = open(wordFilePath, 'r')

        obj = site.PUT_factory('test', 'application/msword', wordFile)
        site._setObject('test', obj)

        obj = site['test']
        request = site.REQUEST
        request['BODYFILE'] = wordFile
        obj.PUT()

        wordFile.seek(0)
        data = wordFile.read()

        word = site.test

        self.assertEqual(word.archetype_name, DDocument.archetype_name)
        self.assertEqual(str(word.getBody(raw=1)), data)


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
