import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_widgets',
                                 'Cannot import ArcheSiteTestCase')

from os import curdir
from os.path import join, abspath, dirname, split

try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

stub_text_file = None
stub_text_content = ''
stub_bin_file = None
stub_bin_content = ''

from Products.Archetypes.public import *
from OFS.Image import File
from DateTime import DateTime
from Acquisition import aq_base

from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.Archetypes.tests.test_fields import FakeRequest


class WidgetTests(ArcheSiteTestCase):

    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager(None, user)
        global stub_text_file, stub_text_content, \
               stub_bin_file, stub_bin_content
        stub_text_file = file(join(_prefix, 'input', 'rest1.rst'))
        stub_text_content = stub_text_file.read()
        stub_text_file.seek(0)
        stub_bin_file = file(join(_prefix, 'input', 'word.doc'))
        stub_bin_content = stub_bin_file.read()
        stub_bin_file.seek(0)

    def test_subject_keyword_widget(self):
        site = self.getPortal()
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['subject']
        widget = field.widget
        form = {'subject_keywords':['bla','ble'],
                'subject_existing_keywords':['bli']
                }
        expected = ['bla', 'ble', 'bli']
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords':['bla'],
                'subject_existing_keywords':['ble','bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords':[],
                'subject_existing_keywords':['bla', 'ble','bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords':['bla', 'ble','bli'],
                'subject_existing_keywords':['bla', 'ble','bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords':['bla', 'ble','bli'],
                'subject_existing_keywords':[]
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])


    def test_widgets(self):
        site = self.getPortal()
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')

        #Now render this doc in view and edit modes. If this works
        #then we have pretty decent assurance that things are working
        view = doc.base_view()
        edit = doc.base_edit()

        #No exceptions are good, parse the results more if you need to
        #I feel fine...

    def test_rich_text_widget(self):
        site = self.getPortal()
        request = FakeRequest()
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['richtextfield']
        widget = field.widget
        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':stub_bin_file,
                'richtextfield':'',
                }
        expected = stub_bin_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':stub_bin_file,
                'richtextfield':stub_text_file,
                }
        expected = stub_bin_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':stub_text_file,
                'richtextfield':'',
                }
        expected = stub_text_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':stub_text_file,
                'richtextfield':stub_text_content,
                }
        expected = stub_text_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)


        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':'',
                'richtextfield':stub_text_content,
                }
        expected = stub_text_content, {'mimetype':'text/x-rst'}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_file':stub_text_file}
        request.form.update(form)
        doc.processForm(REQUEST=request)
        self.assertEqual(field.getContentType(doc), 'text/x-rst')

        form = {'richtextfield_file':stub_bin_file}
        request.form.update(form)
        doc.processForm(REQUEST=request)
        self.assertEqual(field.getContentType(doc), 'application/msword')
        self.assertEqual(str(doc[field.getName()]), stub_bin_content)

        form = {'richtextfield_text_format':'text/x-rst',
                'richtextfield_file':'',
                'richtextfield':stub_text_content,
                }
        expected = stub_text_content, {'mimetype':'text/x-rst'}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format':'',
                'richtextfield_file':'',
                'richtextfield':stub_text_content,
                }
        expected = stub_text_content, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format':'text/plain',
                'richtextfield_file':stub_text_file,
                }
        request.form.update(form)
        doc.processForm(REQUEST=request)
        self.assertEqual(field.getContentType(doc), 'text/x-rst')
        self.assertEqual(str(doc[field.getName()]), stub_text_content)

    def beforeTearDown(self):
        global stub_text_file, stub_bin_file
        stub_text_file.close()
        stub_bin_file.close()
        ArcheSiteTestCase.beforeTearDown(self)

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
