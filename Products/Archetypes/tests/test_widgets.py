import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from OFS.Image import File
from DateTime import DateTime
from Acquisition import aq_base

import ClientForm
import urllib2

from Products.CMFPlone.Portal import manage_addSite

from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.Archetypes.tests.test_sitepolicy import makeContent
from thread import start_new_thread
from utils import start_http

import unittest

field_values = {'objectfield':'objectfield',
                'stringfield':'stringfield',
                'filefield':'filefield',
                'textfield':'textfield',
                'datetimefield':'2003-01-01',
                'linesfield':'bla\nbla',
                'integerfield':'1',
                'floatfield':'1.5',
                'fixedpointfield': '1.5',
                'booleanfield':'1'}

expected_values = {'objectfield':'objectfield',
                   'stringfield':'stringfield',
                   'filefield':'filefield',
                   'textfield':'textfield',
                   'datetimefield':DateTime('2003-01-01'),
                   'linesfield':['bla', 'bla'],
                   'integerfield': 1,
                   'floatfield': 1.5,
                   'fixedpointfield': '1.50',
                   'booleanfield': 1}


class WidgetTests( SecurityRequestTest ):

    def setUp(self):
        SecurityRequestTest.setUp(self)
        try:
            self.root.manage_delObjects(ids=('testsite',))
        except:
            pass
        manage_addSite( self.root, 'testsite', \
                        custom_policy='Archetypes Site' )
        start_new_thread(start_http, ('127.0.0.1', 8080))

    def test_widgets(self):
        site = self.root.testsite
        obj_id = 'demodoc'
        doc = makeContent(site, portal_type='ComplexType', id=obj_id)
        get_transaction().commit()
        request = urllib2.Request("http://127.0.0.1:8080/testsite/demodoc/portal_form/base_edit")
        response = urllib2.urlopen(request)
        forms = ClientForm.ParseResponse(response)
        form = forms[0]
        for f in forms:
            print f

    def tearDown(self):
        self.root._delObject('testsite',)
        SecurityRequestTest.tearDown(self)
        try:
            from ZServer.medusa.asyncore import socket_map
            for k in socket_map.keys():
                socket_map[k].close()
        except ImportError:
            from Lifetime import shutdown
            shutdown(exit_code=0, fast=1)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WidgetTests),
        ))

if __name__ == '__main__':
    unittest.main()
