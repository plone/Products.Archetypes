import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_widgets', 'Cannot import ArcheSiteTestCase')

from Products.Archetypes.public import *
from OFS.Image import File
from DateTime import DateTime
from Acquisition import aq_base

try:
    import ClientForm
except ImportError:
    raise TestPreconditionFailed('test_widgets', 'Cannot import ClientForm')
import urllib2


from Products.Archetypes.tests.test_sitepolicy import makeContent
from thread import start_new_thread
from utils import start_http

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

class WidgetTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager( None, user )
        start_new_thread(start_http, ('127.0.0.1', 50080))

    def test_widgets(self):
        site = self.root.testsite
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')
        get_transaction().commit()
        request = urllib2.Request("http://127.0.0.1:50080/testsite/demodoc/base_edit")
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
        request = urllib2.Request("http://127.0.0.1:50080/testsite/demodoc/base_edit")
        response = urllib2.urlopen(request)
        forms = ClientForm.ParseResponse(response)
        form = findEditForm(forms)
        self.failIf(form is None)
        for k,v in expected_values.items():
            control = form.find_control(k)
            assert form[k] == v, 'Expected %s on %s, got %s' % (v, k, form[k])

    def beforeTearDown(self):
        self.root._delObject('testsite',)
        SecurityRequestTest.tearDown(self)
        try:
            from ZServer.medusa.asyncore import socket_map
            for k in socket_map.keys():
                socket_map[k].close()
        except ImportError:
            from Lifetime import shutdown
            shutdown(exit_code=0, fast=1)
        ArchetypesTestCase.beforeTearDown(self)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(WidgetTests))
        return suite
