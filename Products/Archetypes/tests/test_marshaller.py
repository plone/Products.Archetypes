# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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

"""
Unittests for marshaller

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.atapi import *

from Products.Archetypes import config
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

    # XXX this test is fu... up the machine by eating all memory
    def XXX_test_textFieldObjectWordReplace(self):
        #test that uploading to an existing object works
        obj1 = makeContent(self.folder, portal_type='DDocument', id='obj1')

        wordFilePath = join(PACKAGE_HOME, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')
        data = wordFile.read()
        wordFile.seek(0)

        # put requests don't have the luxury of being able to specify a
        # content type
        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        word = self.folder.obj1
        word.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(word.getContentType('body'), 'application/msword')
        self.assertEqual(word.getRawBody(), data)

    def test_textFieldObjectRSTreplace(self):
        ## And again with an RST
        obj1 = makeContent(self.folder, portal_type='DDocument', id='obj1')

        rstFilePath = join(PACKAGE_HOME, "input", "rest1.rst")
        rstFile = open(rstFilePath, 'r')
        data = rstFile.read()
        rstFile.seek(0)

        request = aputrequest(rstFile, 'text/x-rst')
        # XXX PUT factory is using PARENTS to get an acquisition context
        request['PARENTS'] = (self.folder, self.portal)
        request.processInputs()
        rst = self.folder.obj1
        rst.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(rst.getContentType('body'), 'text/x-rst')
        self.assertEqual(rst.getRawBody().strip(), data.strip())

    def test_fileFieldObjectWordReplace(self):
        #test that uploading to an existing object works
        obj1 = makeContent(self.folder, portal_type='SimpleFile', id='obj1')

        wordFilePath = join(PACKAGE_HOME, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')
        data = wordFile.read()
        wordFile.seek(0)

        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        word = self.folder.obj1
        word.PUT(request, request.RESPONSE)

        #and we can get the stuff back
        self.assertEqual(word.getContentType('body'), 'application/msword')
        self.assertEqual(str(word.getRawBody()), data)

    def setupCTR(self):
        #Modify the CTR to point to SimpleType
        ctr = self.portal.content_type_registry
        if ctr.getPredicate('text'):
            # ATCT has a predict
            ctr.removePredicate('text')
        ctr.addPredicate('text', 'major_minor' )
        ctr.getPredicate('text' ).edit('text', '' )
        ctr.assignTypeName('text', 'DDocument')
        ctr.reorderPredicate('text', 0)

        ctr.addPredicate('msword', 'major_minor' )
        ctr.getPredicate('msword' ).edit( 'application', 'msword' )
        ctr.assignTypeName('msword', 'DDocument')
        ctr.reorderPredicate('msword', 1)

        return ctr

    # XXX this test is fu... up the machine by eating all memory
    def XXX_test_objectCreate(self):
        #create the correct object on upload
        #one day, but this will need a change to the factory
        ctr = self.setupCTR()

        #now trigger the creation of a content type akin to DAV
        wordFilePath = join(PACKAGE_HOME, "input", "word.doc")
        wordFile = open(wordFilePath, 'r')

        obj = self.folder.PUT_factory('test', 'application/msword', wordFile)
        self.folder._setObject('test', obj)
        word = self.folder.test

        request = aputrequest(wordFile, 'application/msword')
        request.processInputs()
        word.PUT(request, request.RESPONSE)

        wordFile.seek(0)
        data = wordFile.read()

        self.assertEqual(word.archetype_name, DDocument.archetype_name)
        self.assertEqual(str(word.getBody(raw=1)), data)
        self.assertEqual(word.getContentType('body'), 'application/msword')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(MarshallerTests))
    return suite

if __name__ == '__main__':
    framework()

