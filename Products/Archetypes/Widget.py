from Acquisition import aq_base

from debug import log
from utils import className, unique, capitalize

try:
    from generator.widget import macrowidget
except:
    from Products.generator.widget import macrowidget


class TypesWidget(macrowidget):
    _properties = macrowidget._properties.copy()
    _properties.update({
        'modes' : ('view', 'edit'),
        'populate' : 1,  # should this field be populated in edit and view?
        'postback' : 1,  # should this field be repopulated with POSTed value when an error occurs?
        })

    def getName(self):
        return self.__class__.__name__

    def getType(self):
        """Return the type of this field as a string"""
        return className(self)

    def bootstrap(self, instance):
        if not self.description or not self.label:
            field = self.findField(instance)
            name = field.getName()
            if not self.label:
                self.label = capitalize(name)
            if not self.description:
                self.description = "Enter a value for %s" % self.label


    def findField(self, instance):
        #This is a sad hack, I don't want widgets to have to take a
        #reference to a field or its own name
        for field in instance.Schema().fields():
            if not hasattr(field, 'widget'):
                continue
            if field.widget is self:
                return field
        return None

    def isVisible(self, instance, mode='view'):
        """decide if a field is visible in a given mode -> 'state' visible, hidden, invisible"""
        # example: visible = { 'edit' :'hidden', 'view' : 'invisible' }
        vis_dic = getattr(aq_base(self), 'visible', None)
        state = 'visible'
        if not vis_dic:
            return state
        state = vis_dic.get(mode, state)
        return state

    def process_form(self, instance, field, form):
        """Basic impl for form processing in a widget"""
        value = form.get(field.getName())
        if not value: return None
        return value, {}


class StringWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/string",
        'size' : '30',
        'maxlength' : '255',
        })

class DecimalWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/decimal",
        'size' : '5',
        })

class IntegerWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/integer",
        'size' : '5',
        })

class ReferenceWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/reference",
        })

class ComputedWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/computed",
        })

class TextAreaWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/textarea",
        'rows'  : 5,
        'cols'  : 40,
        'format': 0,
        })

    def process_form(self, instance, field, form):
        """handle text formatting"""
        text_format = None
        value = None
        # text field with formatting
        value = form.get(field.getName())
        if not value:
            return None

        if hasattr(field, 'allowable_content_types') and \
               field.allowable_content_types:
            text_format = form.get("%s_text_format" % field.getName())
        kwargs = {}

        if text_format:
            kwargs['mimetype'] = text_format

        return value, kwargs

class LinesWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/lines",
        'rows'  : 5,
        'cols'  : 40,
        })

class BooleanWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/boolean",
        })

class CalendarWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/calendar",
        })

class SelectionWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
	'format': "flex", # possible values: flex, select, radio
        'macro' : "widgets/selection",
        })

class MultiSelectionWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
	'format': "select", # possible values: select, checkbox
        'macro' : "widgets/multiselection",
        'size'  : 5,
        })

class KeywordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/keyword",
        'size'  : 5,
        'vocab_source' : 'portal_catalog',
        'roleBasedAdd' : 1,
        })

    def process_form(self, instance, field, form):
        """process keywords from form where this widget has a list of available keywords and any new ones"""
        name = field.getName()
        existing_keywords = form.get('%s_existing_keywords' % name, [])
        new_keywords = form.get('%s_keywords' % name, [])

        value = existing_keywords + new_keywords
        value = [k for k in list(unique(value)) if k]
        return value, {}


class FileWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/file",
        })

    def process_form(self, instance, field, form):
        """form processing that deals with binary data"""
        value = None
        fileobj = form.get('%s_file' % field.getName())
        if fileobj:
            filename = getattr(fileobj, 'filename', '')
            if filename != '':
                value  =  fileobj

        if not value: return None
        return value, {}



class RichWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/rich",
        'rows'  : 5,
        'cols'  : 40,
        'format': 1,
        })

    def process_form(self, instance, field, form):
        """complex form processing, includes handling for text formatting and file objects"""
        # This is basically the old processing chain from base object
        text_format = None
        isFile = 0
        value = None

        # text field with formatting
        if hasattr(field, 'allowable_content_types') and \
           field.allowable_content_types:
            #was a mimetype specified
            text_format = form.get("%s_text_format" % field.getName())

        # or a file?
        fileobj = form.get('%s_file' % field.getName())

        if fileobj:
            filename = getattr(fileobj, 'filename', '')
            if filename != '':
                value  =  fileobj
                isFile = 1

        if not value:
            value = form.get(field.getName())

        if value is None: return None
        kwargs = {}
        kwargs['mimetype'] = text_format
        if instance.isBinary(field.getName()) and not isFile:
            # file field with content, no new content uploaded
            return None

        return value, kwargs


class IdWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/zid",
        'display_autogenerated' : 1,    # show IDs in edit boxes when they are autogenerated?
        'is_autogenerated' : 'isIDAutoGenerated',  # script used to determine if an ID is autogenerated
        })

    def process_form(self, instance, field, form):
        """the id might be hidden by the widget and not submitted"""
        value = form.get('id')
        if not value or not value.strip():
            value = instance.getId()
        return value,  {}

class ImageWidget(FileWidget):
    _properties = FileWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/image",
        'display_threshold': 102400, # only display if size <= threshold, otherwise show link
        })

    def process_form(self, instance, field, form):
        """form processing that deals with image data (and its delete case)"""
        value = None
        ## check to see if the delete hidden was selected
        delete = form.get('%s_delete' % field.getName())
        if delete is not None: return "DELETE_IMAGE", {}

        fileobj = form.get('%s_file' % field.getName())
        if fileobj:
            filename = getattr(fileobj, 'filename', '')
            if filename != '':
                value  =  fileobj

        if not value: return None
        return value, {}


# LabelWidgets are used to display instructions on a form.  The widget only
# displays the label for a value -- no values and no form elements.
class LabelWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/label",
        })

class PasswordWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : 'widgets/password',
        'modes' : ('edit',),
        'populate' : 0,
        'postback' : 0,
        })

class VisualWidget(TextAreaWidget):
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/visual",
        'rows'  : 25,      #rows of TextArea if VE is not available
        'cols'  : 80,      #same for cols
        'width' : '507px', #width of VE frame (if VE is avalilable)
        'height': '400px' ,#same for height
        'format': 0,
        })

class EpozWidget(TextAreaWidget):
    _properties = TextAreaWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/epoz",
        })



__all__ = ('StringWidget', 'DecimalWidget', 'IntegerWidget',
           'ReferenceWidget', 'ComputedWidget', 'TextAreaWidget',
           'LinesWidget', 'BooleanWidget', 'CalendarWidget',
           'SelectionWidget', 'MultiSelectionWidget', 'KeywordWidget',
           'RichWidget', 'FileWidget', 'IdWidget', 'ImageWidget',
           'LabelWidget', 'PasswordWidget', 'VisualWidget', 'EpozWidget',
           )

from Registry import registerWidget

registerWidget(StringWidget,
               title='String',
               description='Renders a HTML text input box which accepts a single line of text',
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerWidget(DecimalWidget,
               title='Decimal',
               description='Renders a HTML text input box which accepts a fixed point value',
               used_for=('Products.Archetypes.Field.FixedPointField',)
               )

registerWidget(IntegerWidget,
               title='Integer',
               description='Renders a HTML text input box which accepts a integer value',
               used_for=('Products.Archetypes.Field.IntegerField',)
               )

registerWidget(ReferenceWidget,
               title='Reference',
               description='Renders a HTML text input box which accepts a reference value',
               used_for=('Products.Archetypes.Field.IntegerField',)
               )

registerWidget(ComputedWidget,
               title='Computed',
               description='Renders the computed value as HTML',
               used_for=('Products.Archetypes.Field.ComputedField',)
               )

registerWidget(TextAreaWidget,
               title='Text Area',
               description='Renders a HTML Text Area for typing a few lines of text',
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.TextField')
               )

registerWidget(LinesWidget,
               title='Lines',
               description='Renders a HTML textarea for a list of values, one per line',
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(BooleanWidget,
               title='Boolean',
               description='Renders a HTML checkbox',
               used_for=('Products.Archetypes.Field.BooleanField',)
               )

registerWidget(CalendarWidget,
               title='Calendar',
               description='Renders a HTML input box with a helper popup box for choosing dates',
               used_for=('Products.Archetypes.Field.DateTimeField',)
               )

registerWidget(SelectionWidget,
               title='Selection',
               description='Renders a HTML selection widget, which can be represented as a dropdown, or as a group of radio buttons',
               used_for=('Products.Archetypes.Field.StringField',
                         'Products.Archetypes.Field.LinesField',)
               )

registerWidget(MultiSelectionWidget,
               title='Multi Selection',
               description='Renders a HTML selection widget, where you can be choose more than one value',
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(KeywordWidget,
               title='Keyword',
               description='Renders a HTML widget for choosing keywords',
               used_for=('Products.Archetypes.Field.LinesField',)
               )

registerWidget(RichWidget,
               title='Rich Widget',
               description='Renders a HTML widget that allows you to type some content, choose formatting and/or upload a file',
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

registerWidget(ImageWidget,
               title='Image',
               description='Renders a HTML widget for uploading/displaying an image',
               used_for=('Products.Archetypes.Field.ImageField',)
               )

registerWidget(LabelWidget,
               title='Label',
               description='Renders a HTML widget that only displays the label',
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

from Registry import registerPropertyType

registerPropertyType('maxlength', 'integer', StringWidget)
registerPropertyType('populate', 'boolean')
registerPropertyType('postback', 'boolean')
registerPropertyType('rows', 'integer', RichWidget)
registerPropertyType('cols', 'integer', RichWidget)
registerPropertyType('rows', 'integer', TextAreaWidget)
registerPropertyType('cols', 'integer', TextAreaWidget)
registerPropertyType('rows', 'integer', LinesWidget)
registerPropertyType('cols', 'integer', LinesWidget)
registerPropertyType('rows', 'integer', VisualWidget)
registerPropertyType('cols', 'integer', VisualWidget)
