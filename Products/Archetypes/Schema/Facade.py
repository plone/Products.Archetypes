__metaclass__ = type

from Products.Archetypes.Schema import BasicSchema
from Products.Archetypes.Field import *
from Products.Archetypes.interfaces.schema import IBindableSchema
from Products.Archetypes.Storage.Facade import FacadeMetadataStorage
from Products.Archetypes.utils import mapply
from Products.Archetypes.ClassGen import generateMethods

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
                  'LinesField':StringField,
                  'LinkField':ObjectField,
                  'ListField':ObjectField,
                  'ListTextAreaField':ObjectField,
                  'MethodField':StringField,
                  'MultiCheckBoxField':LinesField,
                  'MultiListField':StringField,
                  'PasswordField':StringField,
                  'PatternField':StringField,
                  'RadioField':StringField,
                  'RangedIntegerField':StringField,
                  'RawTextAreaField':StringField,
                  'StringField':StringField,
                  'TALESField':StringField,
                  'TextAreaField':StringField}

def getFactory(name):
    return _field_mapping.get(name)

def fieldsFromSet(set, schema):
    fields = {}
    for element in set.getElements():
        factory = getFactory(element.field_type)
        field = factory(element.id,
                        storage=schema.storage,
                        schemata=schema.schemata)
        field.widget.label = element.title_or_id()
        field.widget.description = element.Description()
        field.required = element.isRequired()
        fields[element.id] = field
    return fields

def fieldNamesFromSet(set, schema):
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
        fields = fieldsFromSet(set, obj)
        # XXX This would *really* benefit from some
        # caching/timestamp checking.
        # Calling generateMethods and reconstructing
        # the fields each time may actually be
        # *very very* expensive.
        klass = obj.context.__class__
        generateMethods(klass, fields.values())
        return fields

class CMFMetadataFieldNamesDescriptor:
    """A nice descriptor that computes a set of Archetypes
    fields from a CMFMetadata Set (Formulator-based)"""

    def __get__(self, obj, objtype=None):
        pm = getToolByName(obj.context, 'portal_metadata', None)
        if pm is None:
            return []
        set = pm.getMetadataSet(obj.set_id)
        return fieldNamesFromSet(set, obj)

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
        self.schemata = kwargs['schemata']
        if not kwargs.get('storage'):
            kwargs['storage'] = FacadeMetadataStorage(self.set_id)
        self.storage = kwargs['storage']

    def bind(self, context):
        self.context = context
