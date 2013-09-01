# -*- coding: utf-8 -*-
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
"""
"""

import os

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME
from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.tests.test_fields import FakeRequest
from DateTime import DateTime

stub_text_file = None
stub_text_content = ''
stub_bin_file = None
stub_bin_content = ''


class WidgetTests(ATSiteTestCase):

    def afterSetUp(self):
        # XXX messing up with global vars is bad!
        global stub_text_file, stub_text_content, \
               stub_bin_file, stub_bin_content
        stub_text_file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.rst'))
        stub_text_content = stub_text_file.read()
        stub_text_file.seek(0)
        stub_bin_file = open(os.path.join(PACKAGE_HOME, 'input', 'word.doc'))
        stub_bin_content = stub_bin_file.read()
        stub_bin_file.seek(0)

    def beforeTearDown(self):
        global stub_text_file, stub_bin_file
        stub_text_file.close()
        stub_bin_file.close()

    def test_subject_keyword_widget(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['subject']
        widget = field.widget
        form = {'subject_keywords': ['bla', 'ble'],
                'subject_existing_keywords': ['bli']
                }
        expected = ['bla', 'ble', 'bli']
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords': ['bla'],
                'subject_existing_keywords': ['ble', 'bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords': [],
                'subject_existing_keywords': ['bla', 'ble', 'bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords': ['bla', 'ble', 'bli'],
                'subject_existing_keywords': ['bla', 'ble', 'bli']
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'subject_keywords': ['bla', 'ble', 'bli'],
                'subject_existing_keywords': []
                }
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])

    def test_subject_keyword_widget2(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['selectionlinesfield3']
        widget = field.widget
        form = {'selectionlinesfield3': ['bla', 'ble']}
        expected = ['bla', 'ble']
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])
        form = {'selectionlinesfield3': 'bla\nble'}
        result = widget.process_form(doc, field, form)
        result[0].sort()
        self.assertEqual(expected, result[0])

    def test_subject_keyword_widget_empty(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['subject']
        widget = field.widget
        empty_marker = object()
        # test when the widget is rendered and returns empty lists
        form = {'subject_keywords': [''],
                'subject_existing_keywords': []
                }
        expected = []
        result = widget.process_form(doc, field, form, empty_marker)
        self.assertEqual(expected, result[0])
        # test when the widget is not rendered
        form = {}
        expected = empty_marker
        result = widget.process_form(doc, field, form, empty_marker)
        self.assertEqual(expected, result)

    def test_unicodeTestIn(self):
        # Test the unicodeTestIn skin script.
        vocab = ['\xc3\xab', u'\xeb', 'maurits']
        self.assertEqual(self.portal.unicodeTestIn('maurits', vocab), True)
        self.assertEqual(self.portal.unicodeTestIn(u'maurits', vocab), True)
        # There is no spoon:
        self.assertEqual(self.portal.unicodeTestIn('spoon', vocab), False)

        # This is the most tricky one, as it runs the danger of
        # raising a UnicodeDecodeError (python2.4) or giving a
        # UnicodeWarning (python2.6) which again might raise an
        # Unauthorized error due to guarded_import restrictions.
        self.assertEqual(self.portal.unicodeTestIn(u'\xeb', vocab), True)

        # The unicodeTestIn script can be called very often on edit
        # forms when you have lots of keywords (Subject) in your site.
        # So an interesting test here is: how fast is this?  For a
        # speed test, uncomment the next few lines.  It basically
        # tests having 3000 keywords, of which 50 are selected on a
        # page.  The related change in unicodeTestIn speeds this up
        # from 42 to 15 seconds.
        #vocab += [str(x) for x in range(3000)]
        #for x in range(1000, 1050):
        #    self.assertEqual(self.portal.unicodeTestIn(str(x), vocab), True)

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

        form = {'textarea_appendonly': ''}
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

    def test_appendtextarea_timestamp_widget(self):
        """ This is a test I can write """
        request = FakeRequest()
        mystring = str('<<<<this is a test string>>>>')

        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['textarea_appendonly_timestamp']
        widget = field.widget

        form = {'textarea_appendonly_timestamp': ''}
        result = widget.process_form(doc, field, form)
        expected = '', {}
        self.assertEqual(expected, result)

        form = {'textarea_appendonly_timestamp': mystring}
        expected = mystring, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        doc.Schema()[field.getName()].set(doc, mystring)
        form = {'textarea_appendonly_timestamp': mystring}
        expectation = mystring + '\n\n' + str(DateTime()) + widget.divider + mystring, {}
        results = widget.process_form(doc, field, form)

        # some magic (nightmares?) here for rectifying DateTime delay
        result = results[0].split('\n\n')
        expected = expectation[0].split('\n\n')

        result[1] = result[1].split(' ')
        expected[1] = expected[1].split(' ')

        result[1][1] = expected[1][1][:-3]
        expected[1][1] = expected[1][1][:-3]

        self.assertEqual(expected, result)

    def test_maxlength_textarea_widget(self):
        """ Show me HOW to write this test and I will ~Spanky """

        request = FakeRequest()
        mystring = str('The little black dog jumped over the sleeping Moose')

        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['textarea_maxlength']
        widget = field.widget

        form = {'textarea_maxlength': ''}
        result = widget.process_form(doc, field, form)
        expected = '', {}
        self.assertEqual(expected, result)

        form = {'textarea_maxlength': mystring}
        expected = mystring, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        doc.Schema()[field.getName()].set(doc, mystring)
        form = {'textarea_maxlength': mystring}
        expected = 'The little black dog', {}
        result = widget.process_form(doc, field, form)
        #self.assertEqual(expected, result)

    def test_rich_text_widget(self):
        request = FakeRequest()
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field = doc.Schema()['richtextfield']
        widget = field.widget
        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': stub_bin_file,
                'richtextfield': '',
                }
        expected = stub_bin_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': stub_bin_file,
                'richtextfield': stub_text_file,
                }
        expected = stub_bin_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': stub_text_file,
                'richtextfield': '',
                }
        expected = stub_text_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': stub_text_file,
                'richtextfield': stub_text_content,
                }
        expected = stub_text_file, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': '',
                'richtextfield': stub_text_content,
                }
        expected = stub_text_content, {'mimetype': 'text/x-rst'}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_file': stub_text_file}
        request.form.update(form)
        doc.processForm(REQUEST=request)
        self.assertEqual(field.getContentType(doc), 'text/x-rst')

        # XXX: This makes wv-1.0.3 spin.
        #form = {'richtextfield_file': stub_bin_file}
        #request.form.update(form)
        #doc.processForm(REQUEST=request)
        #self.assertEqual(field.getContentType(doc), 'application/msword')
        #self.assertEqual(str(doc[field.getName()]), stub_bin_content)

        form = {'richtextfield_text_format': 'text/x-rst',
                'richtextfield_file': '',
                'richtextfield': stub_text_content,
                }
        expected = stub_text_content, {'mimetype': 'text/x-rst'}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': '',
                'richtextfield_file': '',
                'richtextfield': stub_text_content,
                }
        expected = stub_text_content, {}
        result = widget.process_form(doc, field, form)
        self.assertEqual(expected, result)

        form = {'richtextfield_text_format': 'text/plain',
                'richtextfield_file': stub_text_file,
                }
        request.form.update(form)
        doc.processForm(REQUEST=request)
        self.assertEqual(field.getContentType(doc), 'text/x-rst')
        self.assertEqual(str(doc[field.getName()]), stub_text_content)

    def test_getBestIcon(self):
        doc = makeContent(self.folder, 'SimpleType', id='doc')
        self.assertEqual(doc.getBestIcon(), 'txt.png')

    def test_vocabulary_enforced(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field_name = 'selectionlinesfield1'
        field = doc.Schema()[field_name]
        # Try a wrong key
        errors = {}
        field.validate(['spoon'], doc, errors)
        self.assertTrue(field_name in errors)
        # Try a correct key
        errors = {}
        field.validate(['foo'], doc, errors)
        self.assertTrue(field_name not in errors)
        # Try a correct key as simple string
        errors = {}
        field.validate('foo', doc, errors)
        self.assertTrue(field_name not in errors)

    def test_vocabulary_display(self):
        # Displaying the value of a vocabulary means checking if the
        # key is in there, getting the value for the key, possibly
        # translate it if it is a message id or try to translate it
        # anyway if the value is a simple string.  This may be tricky,
        # as can be seen in https://dev.plone.org/ticket/7627
        #
        # Note that below you may see some really strange looking
        # results, but that is because during the tests a test
        # translation domain factory is used as fallback, which simply
        # reports the domain and the original msgid in square
        # brackets, without looking up actual translations.  The good
        # thing is that now we can easily check if a translation has
        # been tried for the correct domain and if translation has not
        # been done twice.
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field_name = 'selectionlinesfield1'
        field = doc.Schema()[field_name]
        widget = field.widget
        vocab = field.Vocabulary(doc)
        # This view can be used for displaying and translating a value.
        trans = doc.restrictedTraverse('@@at_utils').translate

        # The key 'foo' has the value 'Foo' and we also try to
        # translate it in the plone domain.  XXX Not sure if that last
        # part is really wanted.  It might be an okay default though.
        result = trans(vocab, ['foo'], widget)
        self.assertEqual(result, u'[[plone][Foo]]')
        result = trans(vocab, ['complex'], widget)
        self.assertEqual(result, u'[[plone][C\xf6mpl\xe8x]]')
        # For the next two, the values are message ids.
        result = trans(vocab, ['bar'], widget)
        self.assertEqual(result, u'[[domain1][Bar]]')
        result = trans(vocab, ['hello'], widget)
        self.assertEqual(result, u'[[domain2][Hello]]')
        # Try a non-existing value.
        result = trans(vocab, ['spoon'], widget)
        self.assertEqual(result, u'[[plone][spoon]]')

        # We try the displayValue Python skin script as well, which
        # serves as a front for the new @@at_utils view.
        result = doc.displayValue(vocab, ['foo'], widget)
        self.assertEqual(result, u'[[plone][Foo]]')
        result = doc.displayValue(vocab, ['complex'], widget)
        self.assertEqual(result, u'[[plone][C\xf6mpl\xe8x]]')
        # For the next two, the values are message ids.
        result = doc.displayValue(vocab, ['bar'], widget)
        self.assertEqual(result, u'[[domain1][Bar]]')
        result = doc.displayValue(vocab, ['hello'], widget)
        self.assertEqual(result, u'[[domain2][Hello]]')
        # Try a non-existing value.
        result = doc.displayValue(vocab, ['spoon'], widget)
        self.assertEqual(result, u'[[plone][spoon]]')

    def test_vocabulary_alternate_domain(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field_name = 'selectionlinesfield2'
        field = doc.Schema()[field_name]
        widget = field.widget
        vocab = field.Vocabulary(doc)
        trans = doc.restrictedTraverse('@@at_utils').translate
        result = trans(vocab, ['foo'], widget)
        self.assertEqual(result, u'[[attesti18n][Foo]]')
        result = trans(vocab, ['complex'], widget)
        self.assertEqual(result, u'[[attesti18n][C\xf6mpl\xe8x]]')
        # For the next two, the values are message ids.
        result = trans(vocab, ['bar'], widget)
        self.assertEqual(result, u'[[domain1][Bar]]')
        result = trans(vocab, ['hello'], widget)
        self.assertEqual(result, u'[[domain2][Hello]]')
        # Try a non-existing value.
        result = trans(vocab, ['spoon'], widget)
        self.assertEqual(result, u'[[attesti18n][spoon]]')

    def test_vocabulary_multi_selection(self):
        doc = makeContent(self.folder, portal_type='ComplexType', id='demodoc')
        field_name = 'selectionlinesfield3'
        field = doc.Schema()[field_name]
        widget = field.widget
        vocab = field.Vocabulary(doc)
        trans = doc.restrictedTraverse('@@at_utils').translate
        result = trans(vocab, ['foo2'], widget)
        self.assertEqual(result, u'[[attesti18n][Foo 2]]')
        result = trans(vocab, ['complex2'], widget)
        self.assertEqual(result, u'[[attesti18n][C\xf6mpl\xe8x 2]]')
        # For the next two, the values are message ids.
        result = trans(vocab, ['bar2'], widget)
        self.assertEqual(result, u'[[domain1][Bar 2]]')
        result = trans(vocab, ['hello2'], widget)
        self.assertEqual(result, u'[[domain2][Hello 2]]')
        # Try a non-existing value.
        result = trans(vocab, ['spoon2'], widget)
        self.assertEqual(result, u'[[attesti18n][spoon2]]')
        # Combine all.
        result = trans(vocab, ['complex2','bar2', 'spoon2'], widget)
        self.assertEqual(result,
            u'[[attesti18n][C\xf6mpl\xe8x 2]], [[domain1][Bar 2]], [[attesti18n][spoon2]]')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(WidgetTests))
    return suite
