# -*- coding: utf-8 -*-
from DateTime import DateTime
from Products.Archetypes.atapi import BaseContent
from Products.Archetypes.atapi import ReferenceField
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.CMFCore.utils import getToolByName
from datetime import datetime
from mock import Mock
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.content.browser.vocabulary import VocabularyView
from plone.app.widgets.testing import PLONEAPPWIDGETS_INTEGRATION_TESTING
from plone.app.widgets.testing import TestRequest
from plone.testing.zca import ZCML_DIRECTIVES
from zope.configuration import xmlconfig
from zope.globalrequest import setRequest

import json
import mock

try:
    import unittest2 as unittest
except ImportError:  # pragma: nocover
    import unittest  # pragma: nocover
    assert unittest  # pragma: nocover

import plone.uuid


class BaseWidgetTests(unittest.TestCase):

    def test_widget_pattern_notimplemented(self):
        from Products.Archetypes.Widget import BasePatternWidget
        from plone.app.widgets.utils import NotImplemented

        widget = BasePatternWidget()

        with self.assertRaises(NotImplemented):
            widget._base_args(None, None, None)

        widget.pattern = 'example'

        self.assertEqual(
            {
                'pattern': 'example',
                'pattern_options': {}
            },
            widget._base_args(None, None, None))

    def test_widget_base_notimplemented(self):
        from Products.Archetypes.Widget import BasePatternWidget
        from plone.app.widgets.base import InputWidget
        from plone.app.widgets.utils import NotImplemented

        widget = BasePatternWidget(pattern='example')

        with self.assertRaises(NotImplemented):
            widget.edit(None, None, None)

        widget._base = InputWidget

        self.assertEqual(
            '<input class="pat-example" type="text"/>',
            widget.edit(None, None, None))


class DateWidgetTests(unittest.TestCase):

    def setUp(self):
        from Products.Archetypes.Widget import DateWidget
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.context = Mock()
        self.field = Mock()
        self.field.getAccessor.return_value = lambda: u''
        self.field.getName.return_value = 'fieldname'
        self.widget = DateWidget()

    def test_widget(self):
        current_year = datetime.today().year
        self.assertEqual(
            {
                'pattern': 'pickadate',
                'value': u'',
                'name': 'fieldname',
                'pattern_options': {
                    'date': {
                        'firstDay': 0,
                        'min': [current_year - 100, 1, 1],
                        'max': [current_year + 20, 1, 1],
                        'format': 'mmmm d, yyyy',
                        'monthsFull': [u'January', u'February', u'March',
                                       u'April', u'May', u'June', u'July',
                                       u'August', u'September', u'October',
                                       u'November', u'December'],
                        'weekdaysShort': [u'Sun', u'Mon', u'Tue', u'Wed',
                                          u'Thu', u'Fri', u'Sat'],
                        'weekdaysFull': [u'Sunday', u'Monday', u'Tuesday',
                                         u'Wednesday', u'Thursday', u'Friday',
                                         u'Saturday'],
                        'selectYears': 200,
                        'placeholder': u'Enter date...',
                        'monthsShort': [u'Jan', u'Feb', u'Mar', u'Apr', u'May',
                                        u'Jun', u'Jul', u'Aug', u'Sep', u'Oct',
                                        u'Nov', u'Dec']
                    },
                    'time': False,
                    'today': u'Today',
                    'clear': u'Clear',

                }
            },
            self.widget._base_args(self.context, self.field, self.request),
        )

    def test_process_form(self):
        form = {
            'fieldname': '2011-11-22',
        }
        self.assertEqual(
            self.widget.process_form(
                self.context, self.field, form)[0].asdatetime(),
            (datetime(2011, 11, 22))
        )

    def test_process_form_empty_existing(self):
        form = {
            'fieldname': ''
        }
        self.assertEqual(
            self.widget.process_form(
                self.context, self.field, form)[0],
            None
        )


class DatetimeWidgetTests(unittest.TestCase):

    def setUp(self):
        from Products.Archetypes.Widget import DatetimeWidget
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.context = Mock()
        self.field = Mock()
        self.field.getAccessor.return_value = lambda: DateTime(
            '2013-11-13 10:20 Europe/Amsterdam'
        )
        self.field.getName.return_value = 'fieldname'
        self.widget = DatetimeWidget()

    def test_widget(self):
        current_year = datetime.today().year
        self.assertEqual(
            {
                'pattern': 'pickadate',
                'value': '2013-11-13 10:20',
                'name': 'fieldname',
                'pattern_options': {
                    'date': {
                        'firstDay': 0,
                        'min': [current_year - 100, 1, 1],
                        'max': [current_year + 20, 1, 1],
                        'format': 'mmmm d, yyyy',
                        'monthsFull': [u'January', u'February', u'March',
                                       u'April', u'May', u'June', u'July',
                                       u'August', u'September', u'October',
                                       u'November', u'December'],
                        'weekdaysShort': [u'Sun', u'Mon', u'Tue', u'Wed',
                                          u'Thu', u'Fri', u'Sat'],
                        'weekdaysFull': [u'Sunday', u'Monday', u'Tuesday',
                                         u'Wednesday', u'Thursday', u'Friday',
                                         u'Saturday'],
                        'selectYears': 200,
                        'placeholder': u'Enter date...',
                        'monthsShort': [u'Jan', u'Feb', u'Mar', u'Apr', u'May',
                                        u'Jun', u'Jul', u'Aug', u'Sep', u'Oct',
                                        u'Nov', u'Dec']
                    },
                    'time': {
                        'placeholder': u'Enter time...',
                        'format': 'h:i a'
                    },
                    'today': u'Today',
                    'clear': u'Clear',
                }
            },
            self.widget._base_args(self.context, self.field, self.request),
        )

    def test_process_form(self):
        form = {
            'fieldname': '2011-11-22 13:30',
        }
        self.assertEqual(
            self.widget.process_form(
                self.context, self.field, form)[0].asdatetime(),
            (datetime(2011, 11, 22, 13, 30))
        )

    def test_process_form_empty_existing(self):
        form = {
            'fieldname': ''
        }
        self.assertEqual(
            self.widget.process_form(
                self.context, self.field, form)[0],
            None
        )


class SelectWidgetTests(unittest.TestCase):

    def setUp(self):
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.context = Mock()
        self.vocabulary = Mock()
        self.vocabulary.items.return_value = [
            ('one', 'one'),
            ('two', 'two'),
            ('three', 'three'),
        ]
        self.field = Mock()
        self.field.getAccessor.return_value = lambda: ()
        self.field.getName.return_value = 'fieldname'
        self.field.Vocabulary.return_value = self.vocabulary

    def test_widget(self):
        from Products.Archetypes.Widget import SelectWidget
        widget = SelectWidget()
        self.assertEqual(
            {
                'multiple': False,
                'name': 'fieldname',
                'pattern_options': {'separator': ';'},
                'pattern': 'select2',
                'value': (),
                'items': [
                    ('one', 'one'),
                    ('two', 'two'),
                    ('three', 'three')
                ]
            },
            widget._base_args(self.context, self.field, self.request),
        )

        widget.multiple = True
        self.assertEqual(
            {
                'multiple': True,
                'name': 'fieldname',
                'pattern_options': {'separator': ';'},
                'pattern': 'select2',
                'value': (),
                'items': [
                    ('one', 'one'),
                    ('two', 'two'),
                    ('three', 'three')
                ]
            },
            widget._base_args(self.context, self.field, self.request),
        )

        self.field.getAccessor.return_value = lambda: u'one'
        self.assertEqual(
            {
                'multiple': True,
                'name': 'fieldname',
                'pattern_options': {'separator': ';'},
                'pattern': 'select2',
                'value': (u'one'),
                'items': [
                    ('one', 'one'),
                    ('two', 'two'),
                    ('three', 'three')
                ]
            },
            widget._base_args(self.context, self.field, self.request),
        )

    def test_widget_orderable(self):
        from Products.Archetypes.Widget import SelectWidget
        widget = SelectWidget()
        widget.multiple = True
        widget.orderable = True
        self.assertEqual(
            {
                'multiple': True,
                'name': 'fieldname',
                'pattern_options': {'orderable': True, 'separator': ';'},
                'pattern': 'select2',
                'value': (),
                'items': [
                    ('one', 'one'),
                    ('two', 'two'),
                    ('three', 'three')
                ]
            },
            widget._base_args(self.context, self.field, self.request),
        )

    def test_process_form(self):
        from Products.Archetypes.Widget import SelectWidget
        widget = SelectWidget()
        form = {'fieldname': 'aaa.bbb.ccc'}
        self.assertEquals('aaa.bbb.ccc',
                          widget.process_form(self.context,
                                              self.field, form)[0])
        widget.multiple = True
        widget.separator = "."
        self.assertEquals(['aaa', 'bbb', 'ccc'],
                          widget.process_form(self.context,
                                              self.field, form)[0])

# TODO
# class AjaxSelectWidgetTests(unittest.TestCase):


class RelatedItemsWidgetTests(unittest.TestCase):

    layer = ZCML_DIRECTIVES

    def setUp(self):

        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.context = Mock(
            absolute_url=lambda: '',
            getPhysicalPath=lambda: ('', 'Plone', 'doc'))
        self.field = Mock()

        xmlconfig.file('configure.zcml', plone.uuid,
                       context=self.layer['configurationContext'])

    def test_multi_valued(self):
        from zope.event import notify
        from zope.interface import implementer
        from zope.lifecycleevent import ObjectCreatedEvent
        from plone.uuid.interfaces import IUUID
        from plone.uuid.interfaces import IAttributeUUID
        from Products.Archetypes.Widget import RelatedItemsWidget

        @implementer(IAttributeUUID)
        class ExampleContent(object):
            pass

        obj1 = ExampleContent()
        obj2 = ExampleContent()
        notify(ObjectCreatedEvent(obj1))
        notify(ObjectCreatedEvent(obj2))

        self.field.getName.return_value = 'fieldname'
        self.field.getAccessor.return_value = lambda: [obj1, obj2]
        self.field.multiValued = True

        widget = RelatedItemsWidget()

        self.assertEqual(
            {
                'name': 'fieldname',
                'value': '{};{}'.format(IUUID(obj1), IUUID(obj2)),
                'pattern': 'relateditems',
                'pattern_options': {
                    'separator': ';',
                    'orderable': True,
                    'maximumSelectionSize': -1,
                    'vocabularyUrl': '/@@getVocabulary?name='
                                     'plone.app.vocabularies.Catalog'
                                     '&field=fieldname',
                    'basePath': '/Plone/doc',
                    'contextPath': '/Plone/doc',
                    'rootPath': '/',
                    'rootUrl': ''
                },
            },
            widget._base_args(self.context, self.field, self.request),
        )

    def test_single_value(self):
        from zope.event import notify
        from zope.interface import implementer
        from zope.lifecycleevent import ObjectCreatedEvent
        from plone.uuid.interfaces import IUUID
        from plone.uuid.interfaces import IAttributeUUID
        from Products.Archetypes.Widget import RelatedItemsWidget

        @implementer(IAttributeUUID)
        class ExampleContent(object):
            pass

        obj1 = ExampleContent()
        notify(ObjectCreatedEvent(obj1))

        self.field.getName.return_value = 'fieldname'
        self.field.getAccessor.return_value = lambda: obj1
        self.field.multiValued = False

        widget = RelatedItemsWidget()

        self.assertEqual(
            {
                'name': 'fieldname',
                'value': '{}'.format(IUUID(obj1)),
                'pattern': 'relateditems',
                'pattern_options': {
                    'separator': ';',
                    'orderable': True,
                    'maximumSelectionSize': 1,
                    'vocabularyUrl': '/@@getVocabulary?name=plone.app.vocabularies.Catalog&field=fieldname',  # noqa
                    'basePath': '/Plone/doc',
                    'contextPath': '/Plone/doc',
                    'rootPath': '/',
                    'rootUrl': ''
                },
            },
            widget._base_args(self.context, self.field, self.request),
        )

    def test_single_valued_empty(self):
        from Products.Archetypes.Widget import RelatedItemsWidget

        self.field.getName.return_value = 'fieldname'
        self.field.getAccessor.return_value = lambda: None
        self.field.multiValued = False

        widget = RelatedItemsWidget()

        self.assertEqual(
            {
                'name': 'fieldname',
                'value': '',
                'pattern': 'relateditems',
                'pattern_options': {
                    'separator': ';',
                    'orderable': True,
                    'maximumSelectionSize': 1,
                    'vocabularyUrl': '/@@getVocabulary?name='
                                     'plone.app.vocabularies.Catalog'
                                     '&field=fieldname',
                    'basePath': '/Plone/doc',
                    'contextPath': '/Plone/doc',
                    'rootPath': '/',
                    'rootUrl': '',
                },
            },
            widget._base_args(self.context, self.field, self.request),
        )

    def test_multiple_widgets(self):
        from zope.event import notify
        from Products.Archetypes.Widget import RelatedItemsWidget
        from zope.interface import implementer
        from zope.lifecycleevent import ObjectCreatedEvent
        from plone.uuid.interfaces import IUUID
        from plone.uuid.interfaces import IAttributeUUID

        @implementer(IAttributeUUID)
        class ExampleContent(object):
            pass

        obj1 = ExampleContent()
        obj2 = ExampleContent()
        notify(ObjectCreatedEvent(obj1))
        notify(ObjectCreatedEvent(obj2))

        self.context.fieldvalue = lambda: obj1

        field1 = ReferenceField(
            'fieldname1',
            relationship="A",
            multiValued=False,
            widget=RelatedItemsWidget(),
        )
        field1.accessor = "fieldvalue"

        self.assertEqual(
            {
                'name': 'fieldname1',
                'value': '{}'.format(IUUID(obj1)),
                'pattern': 'relateditems',
                'pattern_options': {
                    'separator': ';',
                    'orderable': True,
                    'maximumSelectionSize': 1,
                    'vocabularyUrl': '/@@getVocabulary?name='
                                     'plone.app.vocabularies.Catalog'
                                     '&field=fieldname1',
                    'basePath': '/Plone/doc',
                    'contextPath': '/Plone/doc',
                    'rootPath': '/',
                    'rootUrl': '',
                },
            },
            field1.widget._base_args(self.context, field1, self.request),
        )

        field2 = ReferenceField(
            'fieldname2',
            relationship="A",
            multiValued=True,
            widget=RelatedItemsWidget(),
        )
        field2.accessor = "fieldvalue"
        self.context.fieldvalue = lambda: [obj1, obj2]

        self.assertEqual(
            {
                'name': 'fieldname2',
                'value': '{};{}'.format(IUUID(obj1), IUUID(obj2)),
                'pattern': 'relateditems',
                'pattern_options': {
                    'separator': ';',
                    'orderable': True,
                    'maximumSelectionSize': -1,
                    'vocabularyUrl': '/@@getVocabulary?name='
                                     'plone.app.vocabularies.Catalog'
                                     '&field=fieldname2',
                    'basePath': '/Plone/doc',
                    'contextPath': '/Plone/doc',
                    'rootPath': '/',
                    'rootUrl': '',
                },
            },
            field2.widget._base_args(self.context, field2, self.request),
        )


class QueryStringWidgetTests(unittest.TestCase):

    def setUp(self):
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.context = Mock()
        self.context.absolute_url.return_value = ''
        self.field = Mock()

    def test_widget(self):
        from Products.Archetypes.Widget import QueryStringWidget

        self.field.getName.return_value = 'fieldname'
        self.field.getRaw.return_value = [
            {'query': 'string1'},
            {'query': 'string2'},
        ]

        widget = QueryStringWidget()

        self.assertEqual(
            {
                'name': 'fieldname',
                'value': '[{"query": "string1"}, {"query": "string2"}]',
                'pattern': 'querystring',
                'pattern_options': {
                    'indexOptionsUrl': '/@@qsOptions',
                    'previewCountURL': '/@@querybuildernumberofresults',
                    'previewURL': '/@@querybuilder_html_results',
                },
            },
            widget._base_args(self.context, self.field, self.request),
        )


class TinyMCEWidgetTests(unittest.TestCase):

    layer = PLONEAPPWIDGETS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.field = Mock()
        self.field.getAccessor.return_value = lambda: 'fieldvalue'
        self.field.getName.return_value = 'fieldname'
        self.field.getContentType.return_value = 'text/html'

    def test_widget(self):
        # BBB: portal_tinymce is removed in Plone 5. Remove this check when
        # Plone < 5 is no longer supported.
        utility = getToolByName(self.portal, 'portal_tinymce', None)
        if not utility:
            return
        from Products.Archetypes.Widget import TinyMCEWidget
        widget = TinyMCEWidget()
        self.field.widget = widget
        base_args = widget._base_args(self.portal, self.field, self.request)
        self.assertEqual(base_args['name'], 'fieldname')
        self.assertEqual(base_args['value'], 'fieldvalue')
        self.assertEqual(base_args['pattern'], 'tinymce')

    @mock.patch(
        'Products.Archetypes.mimetype_utils.getDefaultContentType',
        new=lambda ctx: 'text/html')
    @mock.patch(
        'Products.Archetypes.mimetype_utils.getAllowedContentTypes',
        new=lambda ctx: ['text/html'])
    def test_at_tinymcewidget_single_mimetype(self):
        """A RichTextWidget with only one available mimetype should render the
        pattern class directly on itself.
        """
        from Products.Archetypes.Widget import TinyMCEWidget
        widget = TinyMCEWidget()
        rendered = widget.edit(self.portal, self.field, self.request)

        self.assertTrue('<select' not in rendered)
        self.assertTrue('pat-tinymce' in rendered)
        self.assertTrue('data-pat-tinymce' in rendered)

    @mock.patch(
        'Products.Archetypes.mimetype_utils.getDefaultContentType',
        new=lambda ctx: 'text/html')
    @mock.patch(
        'Products.Archetypes.mimetype_utils.getAllowedContentTypes',
        new=lambda ctx: ['text/html', 'text/plain'])
    def test_at_tinymcewidget_multiple_mimetypes_create(self):
        """A RichTextWidget with multiple available mimetypes should render a
        mimetype selection widget along with the textfield. When there is no
        field value, the default mimetype should be preselected.
        """
        from Products.Archetypes.Widget import TinyMCEWidget
        widget = TinyMCEWidget()
        rendered = widget.edit(self.portal, self.field, self.request)

        self.assertTrue('<select' in rendered)
        self.assertTrue('pat-textareamimetypeselector' in rendered)
        self.assertTrue('data-pat-textareamimetypeselector' in rendered)
        self.assertTrue(
            '<option value="text/html" selected="selected">' in rendered)
        self.assertTrue('pat-tinymce' not in rendered)


class ArchetypesVocabularyPermissionTests(unittest.TestCase):

    layer = PLONEAPPWIDGETS_INTEGRATION_TESTING

    def setUp(self):
        from Products.Archetypes.Widget import AjaxSelectWidget
        self.request = TestRequest(environ={'HTTP_ACCEPT_LANGUAGE': 'en'})
        setRequest(self.request)
        self.portal = self.layer['portal']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        class TestAT(BaseContent):

            schema = BaseContent.schema.copy() + Schema((
                StringField(
                    'allowed_field',
                    vocabulary_factory='plone.app.vocabularies.PortalTypes',
                    write_permission='View'),
                StringField(
                    'disallowed_field',
                    vocabulary_factory='plone.app.vocabularies.PortalTypes',
                    write_permission='View management screens'),
                StringField(
                    'default_field',
                    vocabulary_factory='plone.app.vocabularies.PortalTypes'),
                StringField(
                    'allowed_widget_vocab',
                    write_permission='View',
                    widget=AjaxSelectWidget(
                        vocabulary='plone.app.vocabularies.PortalTypes'),
                )))

        self.portal._setObject('test_at', TestAT('test_at'),
                               suppress_events=True)

        self.portal.test_at.manage_permission('View',
                                              ('Anonymous',),
                                              acquire=False)
        self.portal.test_at.manage_permission('View management screens',
                                              (),
                                              acquire=False)
        self.portal.test_at.manage_permission('Modify portal content',
                                              ('Editor', 'Manager',
                                               'Site Adiminstrator'),
                                              acquire=False)

    def test_vocabulary_field_allowed(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.PortalTypes',
            'field': 'allowed_field',
        })
        data = json.loads(view())
        self.assertEquals(len(data['results']),
                          len(self.portal.portal_types.objectIds()))

    def test_vocabulary_field_wrong_vocab_disallowed(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.Fake',
            'field': 'allowed_field',
        })
        data = json.loads(view())
        self.assertEquals(data['error'], 'Vocabulary lookup not allowed')

    def test_vocabulary_field_disallowed(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.PortalTypes',
            'field': 'disallowed_field',
        })
        data = json.loads(view())
        self.assertEquals(data['error'], 'Vocabulary lookup not allowed')

    def test_vocabulary_field_default_permission(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.PortalTypes',
            'field': 'default_field',
        })
        # If the field is does not have a security declaration, the
        # default edit permission is tested (Modify portal content)
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        data = json.loads(view())
        self.assertEquals(data['error'], 'Vocabulary lookup not allowed')

        setRoles(self.portal, TEST_USER_ID, ['Editor'])
        # Now access should be allowed, but the vocabulary does not exist
        data = json.loads(view())
        self.assertEquals(len(data['results']),
                          len(self.portal.portal_types.objectIds()))

    def test_vocabulary_field_default_permission_wrong_vocab(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.Fake',
            'field': 'default_field',
        })
        setRoles(self.portal, TEST_USER_ID, ['Editor'])
        # Now access should be allowed, but the vocabulary does not exist
        data = json.loads(view())
        self.assertEquals(data['error'], 'Vocabulary lookup not allowed')

    def test_vocabulary_widget_vocab_allowed(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.PortalTypes',
            'field': 'allowed_widget_vocab',
        })
        data = json.loads(view())
        self.assertEquals(len(data['results']),
                          len(self.portal.portal_types.objectIds()))

    def test_vocabulary_missing_field(self):
        view = VocabularyView(self.portal.test_at, self.request)
        self.request.form.update({
            'name': 'plone.app.vocabularies.PortalTypes',
            'field': 'missing_field',
        })
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        with self.assertRaises(AttributeError):
            view()
