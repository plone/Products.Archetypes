__metaclass__ = type

from Products.Archetypes.Schema import BasicSchema
from Products.Archetypes.Field import *
from Products.Archetypes.interfaces.schema import IBindableSchema

from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName

# XXX Crude mapping for now. We should instantiate
# the right widgets for some specialized fields
# that map better.
_field_mapping = {'CheckBoxField':BooleanField,
                  'DateTimeField':DateTimeField,
                  'EmailField':StringField,
                  'FileField':FileField,
                  'FloatField':FloatField,
                  'IntegerField':IntegerField,
                  'LinesField':LinesField,
                  'LinkField':StringField,
                  'ListField':LinesField,
                  'ListTextAreaField':LinesField,
                  'MethodField':StringField,
                  'MultiCheckBoxField':LinesField,
                  'MultiListField':LinesField,
                  'PasswordField':StringField,
                  'PatternField':StringField,
                  'RadioField':StringField,
                  'RangedIntegerField':StringField,
                  'RawTextAreaField':StringField,
                  'StringField':StringField,
                  'TALESField':StringField,
                  'TextAreaField':StringField}

def fieldsFromSet(set):
    fields = {}
    for element in set.getElements():
        field = _field_mapping.get(element.field_type)(element.id)
        field.widget.label = element.title_or_id()
        field.widget.description = element.Description()
        fields[element.id] = field
    return fields

def fieldNamesFromSet(set):
    fields = []
    for element in set.getElements():
        fields.append(element.id)
    return fields

class CMFMetadataFieldsDescriptor:
    """A nice descriptor that computes a set of Archetypes
    fields from a CMFMetadata Set (Formulator-based)"""

    def __get__(self, obj, objtype=None):
        pm = getToolByName(obj.context, 'portal_metadata', None)
        if pm is None:
            return {}
        set = pm.getMetadataSet(obj.set_id)
        return fieldsFromSet(set)

class CMFMetadataFieldNamesDescriptor:
    """A nice descriptor that computes a set of Archetypes
    fields from a CMFMetadata Set (Formulator-based)"""

    def __get__(self, obj, objtype=None):
        pm = getToolByName(obj.context, 'portal_metadata', None)
        if pm is None:
            return []
        set = pm.getMetadataSet(obj.set_id)
        return fieldNamesFromSet(set)

class FacadeMetadataSchema(BasicSchema):
    """A Facade Schema, which adapts CMFMetadata 'Sets'
    to groups of Archetypes fields
    """

    __implements__ = (IBindableSchema,)

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _names = CMFMetadataFieldNamesDescriptor()
    _fields = CMFMetadataFieldsDescriptor()

    def __init__(self, *args, **kwargs):
        # Everything else is ignored.
        self.set_id = kwargs['set_id']

    def bind(self, context):
        self.context = context
