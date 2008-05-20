__metaclass__ = type

from Products.Archetypes.Schema import BasicSchema
from Products.Archetypes.Field import *
from Products.Archetypes.interfaces.schema import IBindableSchema
from Products.Archetypes.Storage.Facade import FacadeMetadataStorage
from Products.Archetypes.ClassGen import generateMethods

from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View
from zope.interface import implements


# Crude mapping for now. We should instantiate
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

def getFactory(name):
    return _field_mapping.get(name)

def fieldsFromSet(set, schema):
    fields = {}
    for element in set.getElements():
        factory = getFactory(element.field_type)
        name = '%s%s' % (set.id, element.id)
        field = factory(name,
                        metadata_name=element.id,
                        storage=schema.storage,
                        schemata=schema.schemata,
                        default=element.getDefault(schema.context),
                        required=element.isRequired(),
                        isMetadata=schema.isMetadata)
        field.widget.label = element.title_or_id()
        field.widget.description = element.Description()
        fields[name] = field
    return fields

def fieldNamesFromSet(set, schema):
    fields = []
    for element in set.getElements():
        name = '%s%s' % (set.id, element.id)
        fields.append(name)
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
        # TODO This would *really* benefit from some
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

    implements(IBindableSchema)

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
        self.isMetadata = kwargs.get('isMetadata', True)

    def bind(self, context):
        self.context = context

    security.declareProtected(View, 'validate')
    def validate(self, instance=None, REQUEST=None,
                 errors=None, data=None, metadata=None):
        """Validate the state of the entire object.

        The passed dictionary ``errors`` will be filled with human readable
        error messages as values and the corresponding fields' names as
        keys.

        If a REQUEST object is present, validate the field values in the
        REQUEST.  Otherwise, validate the values currently in the object.
        """
        if REQUEST:
            fieldset = REQUEST.form.get('fieldset', None)
        else:
            fieldset = None
        fields = []

        if fieldset is not None:
            schemata = instance.Schemata()
            fields = [(field.getName(), field)
                      for field in schemata[fieldset].fields()]
        else:
            if data:
                fields.extend([(field.getName(), field)
                               for field in self.filterFields(isMetadata=0)])
            if metadata:
                fields.extend([(field.getName(), field)
                               for field in self.filterFields(isMetadata=1)])

        if REQUEST:
            form = REQUEST.form
        else:
            form = None
        _marker = []
        field_data = {}
        for name, field in fields:
            value = None
            widget = field.widget
            if form:
                result = widget.process_form(instance, field, form,
                                             empty_marker=_marker)
            else:
                result = None
            if result is None or result is _marker:
                accessor = field.getAccessor(instance)
                if accessor is not None:
                    value = accessor()
                else:
                    # can't get value to validate -- bail
                    continue
            else:
                value = result[0]
            field_data[name] = value

        pm = getToolByName(self.context, 'portal_metadata', None)
        set = pm.getMetadataSet(self.set_id)
        set.validate(self.set_id, field_data, errors)
        return errors
