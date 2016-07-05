from hashlib import md5

from Products.Archetypes.Schema import Schema
from Products.Archetypes.interfaces.layer import ILayerContainer, \
    ILayerRuntime
from Products.Archetypes.interfaces.schema import ICompositeSchema, \
    IBindableSchema

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import Implicit, aq_parent, aq_inner
from Products.CMFCore.permissions import View, ModifyPortalContent
from zope.interface import implementer


@implementer(ICompositeSchema, ILayerRuntime, ILayerContainer)
class CompositeSchema(Implicit):
    """Act on behalf of a set of Schemas, pretending it
    was a single one.

    Note that if field names overlap, they last schema wins.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, schemas=None):
        self._schemas = [Schema()]
        if schemas is not None:
            self.addSchemas(schemas)

    def getSchemas(self):
        """Return the underlying schemas"""
        schemas = []
        context = aq_parent(aq_inner(self))
        for s in self._schemas:
            if IBindableSchema.providedBy(s):
                s.bind(context)
            schemas.append(s)
        return schemas

    def addSchemas(self, schemas):
        """Append to the underlying schemas"""
        if isinstance(schemas, (list, tuple)):
            schemas = (schemas, )

        for schema in schemas:
            self._schemas.append(schema)

    security.declareProtected(View, 'getName')

    def getName(self):
        """Return Schemata name"""
        return '-'.join([s.getName() for s in self.getSchemas()])

    def __add__(self, other):
        """Add two composite schemas"""
        c = CompositeSchema()
        c.addSchemas((self, other))
        return c

    security.declareProtected(View, 'copy')

    def copy(self):
        """Return a deep copy"""
        c = CompositeSchema()
        c.addSchemas([s.copy() for s in self._schemas()])
        return c

    security.declareProtected(View, 'fields')

    def fields(self):
        """Return a list of fields"""
        result = []
        for s in self.getSchemas():
            result.extend(s.fields())
        return result

    security.declareProtected(View, 'widgets')

    def widgets(self):
        """Return a dictionary that contains a widget for
        each field, using the field name as key.

        Note that if there are fields with the same name, they
        will be overriden by the last schema.
        """
        result = {}
        for s in self.getSchemas():
            result.update(s.widgets())
        return result

    security.declareProtected(View, 'filterFields')

    def filterFields(self, *predicates, **values):
        """Returns a subset of self.fields(), containing only fields that
        satisfy the given conditions.

        You can either specify predicates or values or both. If you provide
        both, all conditions must be satisfied.

        For each ``predicate`` (positional argument), ``predicate(field)`` must
        return 1 for a Field ``field`` to be returned as part of the result.

        Each ``attr=val`` function argument defines an additional predicate:
        A field must have the attribute ``attr`` and field.attr must be equal
        to value ``val`` for it to be in the returned list.
        """
        result = []
        for s in self.getSchemas():
            result.extend(s.filterFields(*predicates, **values))
        return result

    def __setitem__(self, name, field):
        """Add a field under key ``name`` (possibly
        overriding an existing one)
        """
        for s in self.getSchemas():
            if name in s:
                s[name] = field
                return
        self.getSchemas()[0][name] = field

    security.declareProtected(ModifyPortalContent, 'addField')

    def addField(self, field):
        """Add a field (possibly overriding an existing one)"""
        name = field.getName()
        for s in self.getSchemas():
            if name in s:
                s.addField(field)
                return
        self.getSchemas()[0].addField(field)

    security.declareProtected(ModifyPortalContent, 'updateField')
    updateField = addField

    def __delitem__(self, name):
        """Delete field by name ``name`` """
        for s in self.getSchemas():
            if name in s:
                del s[name]
                return
        del self.getSchemas()[0][name]

    security.declareProtected(ModifyPortalContent, 'delField')
    delField = __delitem__

    def __getitem__(self, name):
        """Get field by name.

        Raises KeyError if the field does not exist.
        """
        for s in self.getSchemas():
            if name in s:
                return s[name]
        return self.getSchemas()[0][name]

    security.declareProtected(View, 'get')

    def get(self, name, default=None):
        """Get field by name, using a default value
        for missing
        """
        for s in self.getSchemas():
            if name in s:
                return s.get(name)
        return self.getSchemas()[0].get(name, default)

    security.declareProtected(View, 'has_key')

    def has_key(self, name):
        """Check if a field by the given name exists"""
        for s in self.getSchemas():
            if name in s:
                return True
        return name in self.getSchemas()[0]

    security.declareProtected(View, 'keys')

    def keys(self, name):
        """Return the names of the fields present
        on this schema
        """
        result = []
        for s in self.getSchemas():
            result.extend(s.keys())
        return result

    security.declareProtected(View, 'searchable')

    def searchable(self):
        """Return a list containing names of all
        the fields present on this schema that are
        searchable.
        """
        result = []
        for s in self.getSchemas():
            result.extend(s.searchable())
        return result

    security.declareProtected(ModifyPortalContent, 'edit')

    def edit(self, instance, name, value):
        """Call the mutator by name on instance,
        setting the value.
        """
        if name in self:
            instance[name] = value

    security.declareProtected(ModifyPortalContent, 'setDefaults')

    def setDefaults(self, instance):
        """Only call during object initialization.

        Sets fields to schema defaults.
        """
        for s in self.getSchemas():
            s.setDefaults(instance)

    security.declareProtected(ModifyPortalContent, 'updateAll')

    def updateAll(self, instance, **kwargs):
        """This method mutates fields in the given instance.

        For each keyword argument k, the key indicates the name of the
        field to mutate while the value is used to call the mutator.

        E.g. updateAll(instance, id='123', amount=500) will, depending on the
        actual mutators set, result in two calls: ``instance.setId('123')`` and
        ``instance.setAmount(500)``.
        """
        for s in self.getSchemas():
            s.updateAll(instance, **kwargs)

    security.declareProtected(View, 'allow')
    allow = has_key

    security.declareProtected(ModifyPortalContent, 'validate')

    def validate(self, instance=None, REQUEST=None,
                 errors=None, data=None, metadata=None):
        """Validate the state of the entire object.

        The passed dictionary ``errors`` will be filled with human readable
        error messages as values and the corresponding fields' names as
        keys.
        """
        for s in self.getSchemas():
            s.validate(instance=instance, REQUEST=REQUEST,
                       errors=errors, data=data, metadata=metadata)
        return errors

    security.declarePrivate('toString')

    def toString(self):
        """Utility method for converting a Schema to a string for the
        purpose of comparing schema.

        This is used for determining whether a schema
        has changed in the auto update function.
        """
        result = ''
        for s in self.getSchemas():
            result += s.toString()
        return result

    security.declarePrivate('signature')

    def signature(self):
        """Return an md5 sum of the the schema.

        This is used for determining whether a schema
        has changed in the auto update function.
        """
        return md5(self.toString()).digest()

    security.declarePrivate('changeSchemataForField')

    def changeSchemataForField(self, fieldname, schemataname):
        """Change the schemata for a field """
        for s in self.getSchemas():
            if fieldname in s:
                s.changeSchemataForField(fieldname, schemataname)

    security.declarePrivate('replaceField')

    def replaceField(self, name, field):
        """Replace field under ``name`` with ``field``"""
        for s in self.getSchemas():
            if name in s:
                s.replaceField(name, field)

    security.declarePrivate('initializeLayers')

    def initializeLayers(self, instance, item=None, container=None):
        """Layer initialization"""
        for s in self.getSchemas():
            if ILayerContainer.providedBy(s):
                s.initializeLayers(instance, item, container)

    security.declarePrivate('cleanupLayers')

    def cleanupLayers(self, instance, item=None, container=None):
        """Layer cleaning"""
        for s in self.getSchemas():
            if ILayerContainer.providedBy(s):
                s.cleanupLayers(instance, item, container)

InitializeClass(CompositeSchema)
