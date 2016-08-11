from copy import deepcopy
from datetime import datetime
from types import DictType, FileType, ListType, StringTypes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext

from Products.Archetypes.Registry import registerWidget
from Products.Archetypes.utils import className
from Products.Archetypes.utils import unique
from Products.Archetypes.utils import capitalize
from Products.Archetypes.generator import macrowidget
from Products.Archetypes.log import log
from Products.Archetypes.Registry import registerPropertyType

from ExtensionClass import Base
from App.class_init import InitializeClass
from Acquisition import aq_base

from plone.app.widgets import base as base_widgets
from plone.app.widgets import utils
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID

from zope.component import getUtility

import json

_marker = []


class TypesWidget(macrowidget, Base):
    _properties = macrowidget._properties.copy()
    _properties.update({
        'modes': ('view', 'edit'),
        'populate': True,  # should this field be populated in edit and view?
        'postback': True,  # should this field be repopulated with POSTed
                           # value when an error occurs?
        'show_content_type': False,
        'helper_js': (),
        'helper_css': (),
        'blurrable': False,
    })

    security = ClassSecurityInfo()

    security.declarePublic('getName')

    def getName(self):
        return self.__class__.__name__

    security.declarePublic('getType')

    def getType(self):
        """Return the type of this field as a string"""
        return className(self)

    security.declarePublic('bootstrap')

    def bootstrap(self, instance):
        """Override if your widget needs data from the instance."""
        return

    security.declarePublic('populateProps')

    def populateProps(self, field):
        """This is called when the field is created."""
        name = field.getName()
        if not self.label:
            self.label = capitalize(name)

    security.declarePublic('isVisible')

    def isVisible(self, instance, mode='view'):
        """decide if a field is visible in a given mode -> 'state'

        Return values are visible, hidden, invisible

        The value for the attribute on the field may either be a dict with a
        mapping for edit and view::

            visible = { 'edit' :'hidden', 'view': 'invisible' }

        Or a single value for all modes::

            True/1:  'visible'
            False/0: 'invisible'
            -1:      'hidden'

        visible: The field is shown in the view/edit screen
        invisible: The field is skipped when rendering the view/edit screen
        hidden: The field is added as <input type="hidden" />

        The default state is 'visible'.
        """
        vis_dic = getattr(aq_base(self), 'visible', _marker)
        state = 'visible'
        if vis_dic is _marker:
            return state
        if type(vis_dic) is DictType:
            state = vis_dic.get(mode, state)
        elif not vis_dic:
            state = 'invisible'
        elif vis_dic < 0:
            state = 'hidden'
        return state

    security.declarePublic('setCondition')

    def setCondition(self, condition):
        # Set the widget expression condition.
        self.condition = condition

    security.declarePublic('getCondition')

    def getCondition(self):
        # Return the widget text condition.
        return self.condition

    security.declarePublic('testCondition')

    def testCondition(self, folder, portal, object):
        # Test the widget condition.
        try:
            if self.condition:
                if folder is None and object is not None:
                    folder = aq_parent(aq_inner(object))
                __traceback_info__ = (folder, portal, object, self.condition)
                ec = createExprContext(folder, portal, object)
                return Expression(self.condition)(ec)
            else:
                return True
        except AttributeError:
            return True

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """Basic impl for form processing in a widget"""
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        return value, {}

    security.declarePublic('copy')

    def copy(self):
        """
        Return a copy of widget instance, consisting of field name and
        properties dictionary.
        """
        cdict = dict(vars(self))
        properties = deepcopy(cdict)
        return self.__class__(**properties)

    security.declarePublic('render_own_label')

    def render_own_label(self):
        """
        By default the title/description of a field is not rendered by the
        widget macros, but by the field macros instead. Widgets can change
        that by overriding render_own_label if they need special styling.
        """
        return False

InitializeClass(TypesWidget)


class StringWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/string",
        'size': '30',
        'maxlength': '255',
        'blurrable': True,
        'placeholder': '',
    })

    security = ClassSecurityInfo()


class DecimalWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/decimal",
        'size': '5',
        'maxlength': '255',
        'dollars_and_cents': False,
        'whole_dollars': False,
        'thousands_commas': False,
        'blurrable': True,
        'placeholder': '',
    })

    security = ClassSecurityInfo()


class IntegerWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/integer",
        'size': '5',
        'maxlength': '255',
        'blurrable': True,
        'placeholder': '',
    })

    security = ClassSecurityInfo()


class ReferenceWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/reference",
        'checkbox_bound': 5,

        'addable': False,  # create createObject link for every addable type
        'destination_types': None,
        'destination': None,  # may be:
                              # - ".", context object;
                              # - None, any place where
                              #   Field.allowed_types can be added;
                              # - string path;
                              # - name of method on instance
                              #   (it can be a combination list);
                              # - a list, combining all item above;
                              # - a dict, where
                              #   {portal_type:<combination of the items above>}
                              # destination is relative to portal root
    })

    security = ClassSecurityInfo()

    def lookupDestinationsFor(self, typeinfo, tool, purl, destination_types=None):
        """
        search where the user can add a typeid instance
        """
        searchFor = []

        # first, discover who can contain the type
        if destination_types is not None:
            if type(destination_types) in (type(()), type([])):
                searchFor += list(destination_types[:])
            else:
                searchFor.append(destination_types)
        else:
            for regType in tool.listTypeInfo():
                if typeinfo.globalAllow():
                    searchFor.append(regType.getId())
                elif regType.filter_content_types and regType.allowed_content_types:
                    act_dict = dict([(act, 0)
                                     for act in regType.allowed_content_types])
                    if typeinfo.getId() in act_dict:
                        searchFor.append(regType.getId())

        catalog = getToolByName(purl, 'portal_catalog')
        containers = []
        portal_path = "/".join(purl.getPortalObject().getPhysicalPath())
        for wanted in searchFor:
            for brain in catalog(dict(portal_type=wanted)):
                relative_path = brain.getPath().replace(portal_path + '/', '')
                containers.append(relative_path)

        return containers

    security.declarePublic('addableTypes')

    def addableTypes(self, instance, field):
        """ Returns a list of dictionaries which maps portal_type
            to a human readable form.
        """
        tool = getToolByName(instance, 'portal_types')
        purl = getToolByName(instance, 'portal_url')

        lookupDestinationsFor = self.lookupDestinationsFor
        getRelativeContentURL = purl.getRelativeContentURL

        # if destination_types is None (by default) it will do
        # N-portal_types queries to the catalog which is horribly inefficient

        destination_types = getattr(self, 'destination_types', None)
        destination = self.destination
        types = []

        options = {}
        for typeid in field.allowed_types:
            _info = tool.getTypeInfo(typeid)
            if _info is None:
                # The portal_type asked for was not
                # installed/has been removed.
                log("Warning: in Archetypes.Widget.lookupDestinationsFor: "
                    "portal type %s not found" % typeid)
                continue

            if destination is None:
                options[typeid] = [None]
            elif isinstance(destination, DictType):
                options[typeid] = destination.get(typeid, [None])
                if not isinstance(options[typeid], ListType):
                    options[typeid] = [options[typeid]]
            elif isinstance(destination, ListType):
                options[typeid] = destination
            else:
                place = getattr(aq_base(instance), destination, destination)
                if callable(place):
                    # restore acq.wrapper
                    place = getattr(instance, destination)
                    place = place()
                if isinstance(place, ListType):
                    options[typeid] = place
                else:
                    options[typeid] = [place]

            value = {}
            value['id'] = typeid
            value['name'] = _info.Title()
            value['destinations'] = []

            for option in options.get(typeid):
                if option is None:
                    value['destinations'] = value['destinations'] + \
                        lookupDestinationsFor(_info, tool, purl,
                                              destination_types=destination_types)
                elif option == '.':
                    value['destinations'].append(
                        getRelativeContentURL(instance))
                else:
                    try:
                        place = getattr(aq_base(instance), option, option)
                    except TypeError:
                        place = option
                    if callable(place):
                        # restore acq.wrapper
                        place = getattr(instance, option)
                        place = place()
                    if isinstance(place, ListType):
                        value['destinations'] = place + value['destinations']
                    else:
                        # TODO Might as well check for type, doing it
                        # everywhere else
                        value['destinations'].append(place)

            if value['destinations']:
                types.append(value)

        return types


class ComputedWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/computed",
    })

    security = ClassSecurityInfo()


class TextAreaWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/textarea",
        'rows': 5,
        'cols': 40,
        'format': 0,
        'append_only': False,
        'timestamp': False,
        'divider': "\n\n========================\n\n",
        'timestamp': False,
        'maxlength': False,
        'helper_js': ('widgets/js/textcount.js',),
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """handle text formatting"""
        text_format = None
        value = None
        # text field with formatting
        value = form.get(field.getName(), empty_marker)

        if value is empty_marker:
            return empty_marker

        if emptyReturnsMarker and value == '':
            return empty_marker

        format_field = "%s_text_format" % field.getName()
        text_format = form.get(format_field, empty_marker)
        kwargs = {}

        if text_format is not empty_marker and text_format:
            kwargs['mimetype'] = text_format

        """ handle append_only """
        # Don't append if the existing data is empty or nothing was passed in
        if getattr(field.widget, 'append_only', None):
            if field.getEditAccessor(instance)():
                if (value and not value.isspace()):

                    divider = field.widget.divider

                    # Add a datestamp along with divider if desired.
                    if getattr(field.widget, 'timestamp', None):

                        divider = "\n\n" + str(DateTime()) + divider

                    # using default_output_type caused a recursive transformation
                    # that sucked, thus mimetype= here to keep it in line
                    value = value + divider + \
                        field.getEditAccessor(instance)()
                else:
                    # keep historical entries
                    value = field.getEditAccessor(instance)()
        return value, kwargs


class LinesWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/lines",
        'rows': 5,
        'cols': 40,
    })

    security = ClassSecurityInfo()


class BooleanWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/boolean",
    })

    security = ClassSecurityInfo()


class CalendarWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/calendar",
        'format': '',  # time.strftime string
        'show_hm': True,
        'show_ymd': True,
        'starting_year': None,
        'ending_year': None,
        'future_years': None,
        'minute_step': 5,
        'helper_js': ('jscalendar/calendar_stripped.js',
                      'jscalendar/calendar-en.js'),
        'helper_css': ('jscalendar/calendar-system.css',),
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """Basic impl for form processing in a widget"""

        fname = field.getName()
        value = form.get(fname, empty_marker)
        if value is empty_marker:
            return empty_marker
        # If JS support is unavailable, the value
        # in the request may be missing or incorrect
        # since it won't have been assembled from the
        # input components. Instead of relying on it,
        # assemble the date/time from its input components.
        year = form.get('%s_year' % fname, '0000')
        month = form.get('%s_month' % fname, '00')
        day = form.get('%s_day' % fname, '00')
        hour = form.get('%s_hour' % fname, '00')
        minute = form.get('%s_minute' % fname, '00')
        ampm = form.get('%s_ampm' % fname, '')
        if (year != '0000') and (day != '00') and (month != '00'):
            if ampm and ampm == 'PM' and hour != '12':
                hour = int(hour) + 12
            elif ampm and ampm == 'AM' and hour == '12':
                hour = '00'
            value = "%s-%s-%s %s:%s" % (year, month, day, hour, minute)
        else:
            value = ''
        if emptyReturnsMarker and value == '':
            return empty_marker
        # stick it back in request.form
        form[fname] = value
        return value, {}

    security.declarePublic('render_own_label')

    def render_own_label(self):
        return True


class SelectionWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "flex",  # possible values: flex, select, radio
        'macro': "widgets/selection",
        'blurrable': True,
    })

    security = ClassSecurityInfo()

    security.declarePublic('render_own_label')

    def render_own_label(self):
        return True


class LanguageWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "flex",  # possible values: flex, select, radio
        'macro': "widgets/languagewidget",
        'blurrable': True,
    })

    security = ClassSecurityInfo()


class MultiSelectionWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "select",  # possible values: select, checkbox
        'macro': "widgets/multiselection",
        'size': 5,
        'blurrable': True,
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """Basic impl for form processing in a widget"""
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        if isinstance(value, StringTypes):
            values = [v.strip() for v in value.split('\n')]
        elif isinstance(value, ListType):
            values = value
        else:
            values = []
        return values, {}

    security.declarePublic('render_own_label')

    def render_own_label(self):
        return True


class KeywordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'format': "select",  # possible values: select, checkbox
        'macro': "widgets/keyword",
        'size': 5,
        'vocab_source': 'portal_catalog',
        'roleBasedAdd': True,
        'helper_js': ('widgets/js/keywordmultiselect.js',),
        'helper_css': ('keywordwidget.css',),
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """process keywords from form where this widget has a list of
        available keywords and any new ones"""
        # process_form should return :
        # - a tuple value, kwargs when it did find some value
        # - None or empty_marker when it found nothing
        name = field.getName()
        existing_keywords = form.get('%s_existing_keywords' % name,
                                     empty_marker)
        new_keywords = form.get('%s_keywords' % name, empty_marker)
        if (new_keywords is empty_marker) and (
                existing_keywords is empty_marker):
            return empty_marker
        if new_keywords is empty_marker:
            new_keywords = []
        if existing_keywords is empty_marker:
            existing_keywords = []

        value = existing_keywords + new_keywords
        value = [k for k in list(unique(value)) if k]

        if not value and emptyReturnsMarker:
            return empty_marker

        return value, {}


class FileWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/file",
        'show_content_type': True,
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """form processing that deals with binary data"""

        delete = form.get('%s_delete' % field.getName(), empty_marker)
        if delete == 'delete':
            return "DELETE_FILE", {}

        if delete == 'nochange':
            return empty_marker

        value = None

        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is empty_marker:
            return empty_marker

        filename = getattr(fileobj, 'filename', '')
        if not filename:
            filename = getattr(fileobj, 'name', '')

        if filename:
            value = fileobj

        if not value:
            return None

        return value, {}


class RichWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/rich",
        'rows': 5,
        'cols': 40,
        'format': 1,
        'allow_file_upload': True,
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """complex form processing, includes handling for text
        formatting and file objects"""
        # This is basically the old processing chain from base object
        text_format = None
        isFile = False
        value = None

        # was a mimetype specified
        format_field = "%s_text_format" % field.getName()
        text_format = form.get(format_field, empty_marker)

        # or a file?
        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is not empty_marker:

            filename = getattr(fileobj, 'filename', '') or \
                (isinstance(fileobj, FileType) and
                    getattr(fileobj, 'name', ''))

            if filename:
                value = fileobj
                isFile = True

        kwargs = {}
        if not value:
            value = form.get(field.getName(), empty_marker)
            if text_format is not empty_marker and text_format:
                kwargs['mimetype'] = text_format

        if value is empty_marker:
            return empty_marker

        if value and not isFile:
            # Value filled, no file uploaded
            if (kwargs.get('mimetype') == str(field.getContentType(instance))
                    and instance.isBinary(field.getName())):
                # Was an uploaded file, same content type
                del kwargs['mimetype']

        return value, kwargs


class IdWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/zid",
        # show IDs in edit boxes when they are autogenerated?
        'display_autogenerated': True,
        # script used to determine if an ID is autogenerated
        'is_autogenerated': 'isIDAutoGenerated',
        # ignore global or by-member setting for visible ids?
        'ignore_visible_ids': False,
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """the id might be hidden by the widget and not submitted"""
        value = form.get('id', empty_marker)
        if not value or value is empty_marker or not value.strip():
            value = instance.getId()
        return value,  {}


class RequiredIdWidget(IdWidget):
    _properties = IdWidget._properties.copy()
    _properties.update({
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """Override IdWidget.process_form to require id."""
        return TypesWidget.process_form(self, instance, field, form, empty_marker)


class ImageWidget(FileWidget):
    _properties = FileWidget._properties.copy()
    _properties.update({
        'macro': "widgets/image",
        # only display if size <= threshold, otherwise show link
        'display_threshold': 102400,
        # use this scale for the preview in the edit form, default to 'preview'
        # if this scale isn't available then use the display_threshold
        'preview_scale': 'preview',
    })

    security = ClassSecurityInfo()

    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        """form processing that deals with image data (and its delete case)"""
        value = None
        # check to see if the delete hidden was selected
        delete = form.get('%s_delete' % field.getName(), empty_marker)
        if delete == 'delete':
            return "DELETE_IMAGE", {}

        if delete == 'nochange':
            return empty_marker

        fileobj = form.get('%s_file' % field.getName(), empty_marker)

        if fileobj is empty_marker:
            return empty_marker

        filename = getattr(fileobj, 'filename', '') or \
            (isinstance(fileobj, FileType) and
                getattr(fileobj, 'name', ''))

        if filename:
            value = fileobj

        if not value:
            return None

        return value, {}

    security.declarePublic('preview_tag')

    def preview_tag(self, instance, field):
        """Return a tag for a preview image, or None if no preview is found."""
        img = field.get(instance)
        if not img:
            return None

        if self.preview_scale in field.getAvailableSizes(instance):
            return field.tag(instance, scale=self.preview_scale)

        if img.getSize() <= self.display_threshold:
            return field.tag(instance)

        return None


# LabelWidgets are used to display instructions on a form.  The widget only
# displays the label for a value -- no values and no form elements.
class LabelWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/label",
    })

    security = ClassSecurityInfo()

    security.declarePublic('render_own_label')

    def render_own_label(self):
        return True


class PasswordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': 'widgets/password',
        'modes': ('edit',),
        'populate': False,
        'postback': False,
        'size': 20,
        'maxlength': '255',
    })

    security = ClassSecurityInfo()


class VisualWidget(TextAreaWidget):
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro': "widgets/visual",
        'rows': 25,  # rows of TextArea if VE is not available
        'cols': 80,  # same for cols
        'width': '507px',  # width of VE frame (if VE is avalilable)
        'height': '400px',  # same for height
        'format': 0,
        'append_only': False,  # creates a textarea you can only add to, not edit
        'divider': '\n\n<hr />\n\n',  # default divider for append only divider
    })

    security = ClassSecurityInfo()


class EpozWidget(TextAreaWidget):
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro': "widgets/epoz",
    })

    security = ClassSecurityInfo()


class InAndOutWidget(ReferenceWidget):
    _properties = ReferenceWidget._properties.copy()
    _properties.update({
        'macro': "widgets/inandout",
        'size': '6',
        'helper_js': ('widgets/js/inandout.js',),
    })

    security = ClassSecurityInfo()


class PicklistWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': "widgets/picklist",
        'size': '6',
        'helper_js': ('widgets/js/picklist.js',),
    })

    security = ClassSecurityInfo()


def _one(value, empty_marker=None):
    if isinstance(value, list):
        if len(value) > 0:
            value = value[0]
        else:
            return empty_marker
    return value


class BasePatternWidget(TypesWidget):
    """Base widget for Archetypes."""

    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro': 'patterns_widget',
        'pattern': None,
        'pattern_options': {},
    })

    def _base(self, pattern, pattern_options={}):
        """Base widget class."""
        raise utils.NotImplemented

    def _base_args(self, context, field, request):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options

        :param context: Instance of content type.
        :type context: context

        :param request: Request object.
        :type request: request

        :param field: Instance of field of this widget.
        :type field: field

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        if self.pattern is None:
            raise utils.NotImplemented("'pattern' option is not provided.")
        return {
            'pattern': self.pattern,
            'pattern_options': self.pattern_options,
        }

    def view(self, context, field, request):
        """Render widget on view.

        :returns: Fields value.
        :rtype: string
        """
        return field.getAccessor(context)()

    def edit(self, context, field, request):
        """Render widget on edit.

        :returns: Widget's HTML.
        :rtype: string
        """
        return self._base(**self._base_args(context, field, request)).render()


class DateWidget(BasePatternWidget):
    """Date widget for Archetypes."""

    _base = base_widgets.InputWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'pickadate',
        'pattern_options': {},
    })

    def _base_args(self, context, field, request):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(DateWidget, self)._base_args(context, field, request)
        args['name'] = field.getName()
        args['value'] = (request.get(field.getName(),
                                     field.getAccessor(context)()))

        if args['value'] and isinstance(args['value'], DateTime):
            args['value'] = ('{year:}-{month:02}-{day:02}').format(
                year=args['value'].year(),
                month=args['value'].month(),
                day=args['value'].day(),
            )

        elif args['value'] and isinstance(args['value'], datetime):
            args['value'] = ('{year:}-{month:02}-{day:02}').format(
                year=args['value'].year,
                month=args['value'].month,
                day=args['value'].day,
            )

        args.setdefault('pattern_options', {})
        args['pattern_options'] = base_widgets.dict_merge(
            utils.get_date_options(request),
            args['pattern_options'])

        if 'date' in args['pattern_options'] and \
           'firstDay' in args['pattern_options']['date'] and \
           callable(args['pattern_options']['date']['firstDay']):
            args['pattern_options']['date']['firstDay'] = \
                args['pattern_options']['date']['firstDay']()

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        """Basic impl for form processing in a widget"""

        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker

        value = value.split('-')

        if value[0] == '':
            # empty value, clear any previous value
            return None, {}

        try:
            value = DateTime(datetime(*map(int, value)))
        except:
            return empty_marker

        return value, {}


class DatetimeWidget(DateWidget):
    """Date widget for Archetypes."""

    _properties = DateWidget._properties.copy()
    _properties.update({
        'pattern': 'pickadate',
        'pattern_options': {},
    })

    def _base_args(self, context, field, request):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(DatetimeWidget, self)._base_args(context, field, request)
        args['name'] = field.getName()
        args['value'] = (request.get(field.getName(),
                                     field.getAccessor(context)()))

        if args['value'] and isinstance(args['value'], DateTime):
            args['value'] = (
                '{year:}-{month:02}-{day:02} {hour:02}:{minute:02}'
            ).format(
                year=args['value'].year(),
                month=args['value'].month(),
                day=args['value'].day(),
                hour=args['value'].hour(),
                minute=args['value'].minute(),
            )

        elif args['value'] and isinstance(args['value'], datetime):
            args['value'] = (
                '{year:}-{month:02}-{day:02} {hour:02}:{minute:02}'
            ).format(
                year=args['value'].year,
                month=args['value'].month,
                day=args['value'].day,
                hour=args['value'].hour,
                minute=args['value'].minute,
            )

        if args['value'] and len(args['value'].split(' ')) == 1:
            args['value'] += ' 00:00'

        args.setdefault('pattern_options', {})
        if 'time' in args['pattern_options']:
            del args['pattern_options']['time']
        args['pattern_options'] = base_widgets.dict_merge(
            utils.get_datetime_options(request),
            args['pattern_options'])

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        """Basic impl for form processing in a widget"""

        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker

        tmp = value.split(' ')

        if not tmp[0]:
            # empty: clear, not preserve, any previous value
            return None, {}

        value = tmp[0].split('-')
        if len(tmp) == 2 and ':' in tmp[1]:
            value += tmp[1].split(':')
        else:
            value += ['00', '00']

        try:
            value = DateTime(datetime(*map(int, value)))
        except:
            return empty_marker

        return value, {}


class SelectWidget(BasePatternWidget):
    """Select widget for Archetypes."""

    _base = base_widgets.SelectWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'select2',
        'pattern_options': {},
        'separator': ';',
        'multiple': False,
        'orderable': False,
    })

    def _base_args(self, context, field, request):
        """Method which will calculate _base class arguments.

        Returns (as python dictionary):
            - `pattern`: pattern name
            - `pattern_options`: pattern options
            - `name`: field name
            - `value`: field value
            - `multiple`: field multiple
            - `items`: field items from which we can select to

        :returns: Arguments which will be passed to _base
        :rtype: dict
        """
        args = super(SelectWidget, self)._base_args(context, field, request)
        args['name'] = field.getName()
        args['value'] = (request.get(field.getName(),
                                     field.getAccessor(context)()))
        args['multiple'] = self.multiple

        items = []
        for item in field.Vocabulary(context).items():
            items.append((item[0], item[1]))
        args['items'] = items

        args.setdefault('pattern_options', {})

        if self.separator:
            args['pattern_options']['separator'] = self.separator

        if self.multiple and self.orderable:
            args['pattern_options']['orderable'] = True

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        value = _one(form.get(field.getName(), empty_marker), empty_marker)
        if value is empty_marker:
            return empty_marker
        if self.multiple and isinstance(value, basestring):
            value = value.strip().split(self.separator)
        return value, {}


class AjaxSelectWidget(BasePatternWidget):
    """Ajax select widget for Archetypes."""

    _base = base_widgets.InputWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'select2',
        'pattern_options': {},
        'separator': ';',
        'vocabulary': None,
        'vocabulary_view': '@@getVocabulary',
        'orderable': False,
    })

    def _base_args(self, context, field, request):
        args = super(AjaxSelectWidget, self)._base_args(context, field,
                                                        request)

        vocabulary_factory = getattr(field, 'vocabulary_factory', None)
        if not self.vocabulary:
            self.vocabulary = vocabulary_factory

        args['name'] = field.getName()
        args['value'] = self.separator.join(request.get(
            field.getName(), field.getAccessor(context)()))

        args.setdefault('pattern_options', {})
        args['pattern_options'] = base_widgets.dict_merge(
            utils.get_ajaxselect_options(context, args['value'], self.separator,
                                         self.vocabulary, self.vocabulary_view,
                                         field.getName()),
            args['pattern_options'])

        if self.orderable:
            args['pattern_options']['orderable'] = True

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        value = _one(form.get(field.getName(), empty_marker), empty_marker)
        if value is empty_marker:
            return empty_marker

        value = value.strip().split(self.separator)
        return value, {}


class TagsWidget(AjaxSelectWidget):
    """Keywords widget for Archetypes."""

    _base = base_widgets.InputWidget

    _properties = AjaxSelectWidget._properties.copy()
    _properties.update({
        'vocabulary': 'plone.app.vocabularies.Keywords',
    })

    def _base_args(self, context, field, request):
        args = super(TagsWidget, self)._base_args(context, field,
                                                  request)

        membership = getToolByName(context, 'portal_membership')
        user = membership.getAuthenticatedMember()

        registry = getUtility(IRegistry)
        roles_allowed_to_add_keywords = registry.get(
            'plone.roles_allowed_to_add_keywords', [])

        allowNewItems = False
        if [role for role in user.getRolesInContext(context)
                if role in roles_allowed_to_add_keywords]:
            allowNewItems = True

        args.setdefault('pattern_options', {})
        args['pattern_options']['allowNewItems'] = allowNewItems

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        value = _one(form.get(field.getName(), empty_marker), empty_marker)
        if value is empty_marker:
            return empty_marker
        if not value:
            return [], {}
        value = value.strip().split(self.separator)
        return value, {}


class RelatedItemsWidget(BasePatternWidget):
    """Related items widget for Archetypes."""

    _base = base_widgets.InputWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'relateditems',
        'pattern_options': {},
        'separator': ';',
        'vocabulary': 'plone.app.vocabularies.Catalog',
        'vocabulary_view': '@@getVocabulary',
        'allow_sorting': True,
    })

    def _base_args(self, context, field, request):
        args = super(RelatedItemsWidget, self)._base_args(context, field,
                                                          request)

        value = request.get(field.getName(), None)
        if value is None:
            value = field.getAccessor(context)()
            if field.multiValued:
                value = [IUUID(o) for o in value if o]
            else:
                value = '' if value is None else IUUID(value)
        else:
            value = [v.split('/')[0]
                     for v in value.strip().split(self.separator)]

        vocabulary_factory = getattr(field, 'vocabulary_factory', None)
        if not self.vocabulary:
            self.vocabulary = vocabulary_factory

        args['name'] = field.getName()
        if field.multiValued:
            args['value'] = self.separator.join(value)
        else:
            args['value'] = value

        args.setdefault('pattern_options', {})
        args['pattern_options']['maximumSelectionSize'] = \
            -1 if field.multiValued else 1
        args['pattern_options']['orderable'] = self.allow_sorting
        args['pattern_options'] = base_widgets.dict_merge(
            utils.get_relateditems_options(context, args['value'], self.separator,
                                           self.vocabulary, self.vocabulary_view,
                                           field.getName()),
            args['pattern_options'])

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None):
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        value = [v.split('/')[0] for v in value.strip().split(self.separator)]
        return value, {}


class QueryStringWidget(BasePatternWidget):
    """Query string widget for Archetypes."""

    _base = base_widgets.TextareaWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'querystring',
        'pattern_options': {},
        'querystring_view': '@@qsOptions',
    })

    def _base_args(self, context, field, request):
        args = super(QueryStringWidget, self)._base_args(
            context, field, request)

        args['name'] = field.getName()
        args['value'] = request.get(field.getName(), json.dumps(
            [dict(c) for c in field.getRaw(context)]
        ))

        args.setdefault('pattern_options', {})
        args['pattern_options'] = base_widgets.dict_merge(
            utils.get_querystring_options(context, self.querystring_view),
            args['pattern_options'])

        return args

    security = ClassSecurityInfo()
    security.declarePublic('process_form')

    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False, validating=True):
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        value = json.loads(value)
        return value, {}


class TinyMCEWidget(BasePatternWidget):
    """TinyMCE widget for Archetypes."""

    _base = base_widgets.TextareaWidget

    _properties = BasePatternWidget._properties.copy()
    _properties.update({
        'pattern': 'tinymce',
        'pattern_options': {},
    })

    def _base_args(self, context, field, request):
        args = super(TinyMCEWidget, self)._base_args(context, field, request)
        args['name'] = field.getName()
        args['value'] = (request.get(field.getName(),
                                     field.getAccessor(context)())
                         ).decode('utf-8')

        args.setdefault('pattern_options', {})
        options = base_widgets.dict_merge(
            utils.get_tinymce_options(context, field, request),
            args['pattern_options'])
        args['pattern_options'] = options
        return args

    def edit(self, context, field, request):
        """Render widget on edit.

        :returns: Widget's HTML.
        :rtype: string
        """
        from Products.Archetypes.mimetype_utils import getAllowedContentTypes
        from Products.Archetypes.mimetype_utils import getDefaultContentType
        from lxml import etree

        rendered = ''
        allowed_mime_types = getAllowedContentTypes(context)
        if not allowed_mime_types or len(allowed_mime_types) <= 1:
            # Display textarea with default widget
            rendered = self._base(
                **self._base_args(context, field, request)).render()
        else:
            # Let pat-textarea-mimetype-selector choose the widget

            # Initialize the widget without a pattern
            base_args = self._base_args(context, field, request)
            pattern_options = base_args['pattern_options']
            del base_args['pattern']
            del base_args['pattern_options']
            textarea_widget = self._base(None, None, **base_args)
            textarea_widget.klass = ''
            mt_pattern_name = '{}{}'.format(
                self._base._klass_prefix,
                'textareamimetypeselector'
            )

            # Initialize mimetype selector pattern
            value_mime_type = field.getContentType(context)\
                or getDefaultContentType(context)
            mt_select = etree.Element('select')
            mt_select.attrib['id'] = '{}_text_format'.format(field.getName())
            mt_select.attrib['name'] = '{}_text_format'.format(field.getName())
            mt_select.attrib['class'] = mt_pattern_name
            mt_select.attrib['{}{}'.format('data-', mt_pattern_name)] =\
                json.dumps({
                    'textareaName': field.getName(),
                    'widgets': {
                        'text/html': {  # TODO: currently, we only support
                                        # richtext widget config for
                                        # 'text/html', no other mimetypes.
                            'pattern': self.pattern,
                            'patternOptions': pattern_options
                        }
                    }
                })

            # Create a list of allowed mime types
            for mt in allowed_mime_types:
                opt = etree.Element('option')
                opt.attrib['value'] = mt
                if value_mime_type == mt:
                    opt.attrib['selected'] = 'selected'
                opt.text = mt
                mt_select.append(opt)

            # Render the combined widget
            rendered = '{}\n{}'.format(
                textarea_widget.render(),
                etree.tostring(mt_select)
            )
        return rendered


__all__ = ('StringWidget', 'DecimalWidget', 'IntegerWidget',
           'ReferenceWidget', 'ComputedWidget', 'TextAreaWidget',
           'LinesWidget', 'BooleanWidget', 'CalendarWidget',
           'SelectionWidget', 'MultiSelectionWidget', 'KeywordWidget',
           'RichWidget', 'FileWidget', 'IdWidget', 'ImageWidget',
           'LabelWidget', 'PasswordWidget', 'VisualWidget', 'EpozWidget',
           'InAndOutWidget', 'PicklistWidget', 'RequiredIdWidget',
           'LanguageWidget', 'DateWidget', 'DatetimeWidget',
           'SelectWidget', 'TinyMCEWidget', 'QueryStringWidget',
           'RelatedItemsWidget', 'TagsWidget', 'AjaxSelectWidget'
           )

registerWidget(StringWidget,
               title='String',
               description=('Renders a HTML text input box which '
                            'accepts a single line of text'),
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(DecimalWidget,
               title='Decimal',
               description=('Renders a HTML text input box which '
                            'accepts a fixed point value'),
               used_for=('Products.Archetypes.Field.FixedPointField',)
               )

registerWidget(IntegerWidget,
               title='Integer',
               description=('Renders a HTML text input box which '
                            'accepts a integer value'),
               used_for=('Products.Archetypes.Field.IntegerField',)
               )

registerWidget(ReferenceWidget,
               title='Reference',
               description=('Renders a HTML text input box which '
                            'accepts a reference value'),
               used_for=('Products.Archetypes.Field.ReferenceField',)
               )

registerWidget(ComputedWidget,
               title='Computed',
               description='Renders the computed value as HTML',
               used_for=('Products.Archetypes.Field.ComputedField',)
               )

registerWidget(TextAreaWidget,
               title='Text Area',
               description=('Renders a HTML Text Area for typing '
                            'a few lines of text'),
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.TextField')
               )

registerWidget(LinesWidget,
               title='Lines',
               description=('Renders a HTML textarea for a list '
                            'of values, one per line'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(BooleanWidget,
               title='Boolean',
               description='Renders a HTML checkbox',
               used_for=('Products.Archetypes.Field.BooleanField',)
               )

registerWidget(CalendarWidget,
               title='Calendar',
               description=('Renders a HTML input box with a helper '
                            'popup box for choosing dates'),
               used_for=('Products.Archetypes.Field.DateTimeField',)
               )

registerWidget(SelectionWidget,
               title='Selection',
               description=('Renders a HTML selection widget, which '
                            'can be represented as a dropdown, or as '
                            'a group of radio buttons'),
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.LinesField',)
               )

registerWidget(LanguageWidget,
               title='Language',
               description=('Renders a HTML selection widget for choosing '
                            'a language from a vocabulary. The widget can be '
                            'represented as a dropdown, or as a group of'
                            'of radio buttons'),
               used_for=('Products.Archetypes.Field.StringField')
               )

registerWidget(MultiSelectionWidget,
               title='Multi Selection',
               description=('Renders a HTML selection widget, where '
                            'you can be choose more than one value'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(KeywordWidget,
               title='Keyword',
               description='Renders a HTML widget for choosing keywords',
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(RichWidget,
               title='Rich Widget',
               description=('Renders a HTML widget that allows you to '
                            'type some content, choose formatting '
                            'and/or upload a file'),
               used_for=('Products.Archetypes.Field.TextField',)
               )

registerWidget(FileWidget,
               title='File',
               description='Renders a HTML widget upload a file',
               used_for=('Products.Archetypes.Field.FileField',)
               )

registerWidget(IdWidget,
               title='ID',
               description='Renders a HTML widget for typing an Id',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(RequiredIdWidget,
               title='ID',
               description='Renders a HTML widget for typing an required Id',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(ImageWidget,
               title='Image',
               description=('Renders a HTML widget for '
                            'uploading/displaying an image'),
               used_for=('Products.Archetypes.Field.ImageField',)
               )

registerWidget(LabelWidget,
               title='Label',
               description=('Renders a HTML widget that only '
                            'displays the label'),
               used_for=None
               )

registerWidget(PasswordWidget,
               title='Password',
               description='Renders a HTML password widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(VisualWidget,
               title='Visual',
               description='Renders a HTML visual editing widget widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(EpozWidget,
               title='Epoz',
               description='Renders a HTML Epoz widget',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(InAndOutWidget,
               title='In & Out',
               description=('Renders a widget for moving items '
                            'from one list to another. Items are '
                            'removed from the first list.'),
               used_for=('Products.Archetypes.Field.LinesField',
                         'Products.Archetypes.Field.ReferenceField',)
               )

registerWidget(PicklistWidget,
               title='Picklist',
               description=('Render a widget to pick from one '
                            'list to populate another.  Items '
                            'stay in the first list.'),
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(DateWidget,
               title='Date widget',
               description=('Date widget'),
               used_for=('Products.Archetypes.Field.DateTimeField',))

registerWidget(DatetimeWidget,
               title='Datetime widget',
               description=('Datetime widget'),
               used_for=('Products.Archetypes.Field.DateTimeField',))

registerWidget(SelectWidget,
               title='Select widget',
               description=('Select widget'),
               used_for=('Products.Archetypes.Field.SelectField',))

registerWidget(TinyMCEWidget,
               title='TinyMCE widget',
               description=('TinyMCE widget'),
               used_for='Products.Archetypes.Field.TextField')

registerWidget(QueryStringWidget,
               title='Querystring widget',
               description=('Querystring widget'),
               used_for='archetypes.querywidget.field.QueryField')

registerWidget(RelatedItemsWidget,
               title='Related items widget',
               description=('Related items widget'),
               used_for='Products.Archetypes.Field.ReferenceField')

registerWidget(TagsWidget,
               title='Tags widget',
               description=('Tags widget'),
               used_for=('Products.Archetypes.Field.LinesField',))

registerWidget(AjaxSelectWidget,
               title='Ajax select widget',
               description=('Ajax select widget'),
               used_for=('Products.Archetypes.Field.LinesField',))


registerPropertyType('maxlength', 'integer', StringWidget)
registerPropertyType('populate', 'boolean')
registerPropertyType('postback', 'boolean')
registerPropertyType('rows', 'integer', RichWidget)
registerPropertyType('cols', 'integer', RichWidget)
registerPropertyType('rows', 'integer', TextAreaWidget)
registerPropertyType('cols', 'integer', TextAreaWidget)
registerPropertyType('append_only', 'boolean', TextAreaWidget)
registerPropertyType('divider', 'string', TextAreaWidget)
registerPropertyType('timestamp', 'boolean', TextAreaWidget)
registerPropertyType('rows', 'integer', LinesWidget)
registerPropertyType('cols', 'integer', LinesWidget)
registerPropertyType('rows', 'integer', VisualWidget)
registerPropertyType('cols', 'integer', VisualWidget)
