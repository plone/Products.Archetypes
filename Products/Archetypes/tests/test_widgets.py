import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.Archetypes.tests.common import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_widgets',
                                 'Cannot import ArcheSiteTestCase')

from os import curdir
from os.path import join, abspath, dirname, split

stub_text_file = None
stub_text_content = ''
stub_bin_file = None
stub_bin_content = ''

from Products.Archetypes.public import *
from OFS.Image import File
from DateTime import DateTime

from Products.Archetypes.tests.test_fields import FakeRequest


class WidgetTests(ArcheSiteTestCase):

    def afterSetUp(self):
        global stub_text_file, stub_text_content, \
               stub_bin_file, stub_bin_content
        stub_text_file = file(join(PACKAGE_HOME, 'input', 'rest1.rst'))
        stub_text_content = stub_text_file.read()
        stub_text_file.seek(0)
        stub_bin_file = file(join(PACKAGE_HOME, 'input', 'word.doc'))
        stub_bin_content = stub_bin_file.read()
        stub_bin_file.seek(0)
        # Make SESSION var available
        self.app.REQUEST['SESSION'] = {}

    def test_subject_keyword_widget(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
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

    def _test_widgets(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')

        #Now render this doc in view and edit modes. If this works
        #then we have pretty decent assurance that things are working
        view = doc.base_view()
        edit = doc.base_edit()

        #No exceptions are good, parse the results more if you need to
        #I feel fine...

    def test_appendtextarea_widget(self):
        request = FakeRequest()
        mystring = str('<<<<this is a test string>>>>')
        
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['textarea_appendonly']
        widget = field.widget
        
        form = {'textarea_appendonly':''}
        result = widget.process_form(doc, field, form)
        expected = '', {}
        self.assertEqual(expected, result)
        
        form = {'textarea_appendonly': mystring}
        expected = mystring, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        doc.Schema()[field.getName()].set(doc, mystring)
        form = {'textarea_appendonly': mystring}
        expected = mystring + widget.divider + mystring, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

    def test_rich_text_widget(self):
        request = FakeRequest()
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
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

    def afterClear(self):
        global stub_text_file, stub_bin_file
        stub_text_file.close()
        stub_bin_file.close()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(WidgetTests))
    return suite

if __name__ == '__main__':
    framework()
