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
                'linesfield:lines':'bla\nbla',
                'integerfield':'1',
                'floatfield':'1.5',
                'fixedpointfield': '1.5',
                'booleanfield':'1',
                'selectionlinesfield1':'Test',
                'selectionlinesfield2':'Test',
                }

expected_values = {'objectfield':'objectfield',
                   'stringfield':'stringfield',
                   'filefield':'filefield',
                   'textfield':'textfield',
                   'datetimefield':'2003/01/01',
                   'linesfield:lines':'bla\nbla',
                   'integerfield': '1',
                   'floatfield': '1.5',
                   'fixedpointfield': '1.50',
                   'booleanfield': '1',
                   'selectionlinesfield1':'Test',
                   'selectionlinesfield2':'Test',
                   }


def findEditForm(forms):
    for f in forms:
        if f.action.endswith('base_edit'):
            return f
    return None

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
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')
        get_transaction().commit()
        request = urllib2.Request("http://127.0.0.1:8080/testsite/demodoc/base_edit")
        response = urllib2.urlopen(request)
        forms = ClientForm.ParseResponse(response)
        form = findEditForm(forms)
        self.failIf(form is None)
        for k,v in field_values.items():
            control = form.find_control(k)
            if control and hasattr(control, 'readonly') and control.readonly:
                control.readonly = 0
            form[k] = v
        response = urllib2.urlopen(form.click("form_submit"))
        request = urllib2.Request("http://127.0.0.1:8080/testsite/demodoc/base_edit")
        response = urllib2.urlopen(request)
        forms = ClientForm.ParseResponse(response)
        form = findEditForm(forms)
        self.failIf(form is None)
        for k,v in expected_values.items():
            control = form.find_control(k)
            assert form[k] == v, 'Expected %s on %s, got %s' % (v, k, form[k])

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
