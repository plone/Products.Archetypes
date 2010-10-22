from zope.interface import Interface

class ISchemata(Interface):
    """Schemata (roughly) represents a group of fields"""

    def getName():
        """Return Schemata name"""

    def __add__(other):
        """Add two schematas"""

    def copy():
        """Return a deep copy"""

    def fields():
        """Return a list of fields"""

    def widgets():
        """Return a dictionary that contains a widget for
        each field, using the field name as key
        """

    def filterFields(*predicates, **values):
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

    def __setitem__(name, field):
        """Add a field under key ``name`` (possibly
        overriding an existing one)
        """

    def addField(field):
        """Add a field (possibly overriding an existing one)"""

    def updateField(field):
        """Update a field (possibly overriding an existing one)"""

    def __delitem__(name):
        """Delete field by name ``name`` """

    def delField(name):
        """Delete field by name ``name`` """

    def __getitem__(name):
        """Get field by name.

        Raises KeyError if the field does not exist.
        """

    def get(name, default=None):
        """Get field by name, using a default value
        for missing
        """

    def has_key(name):
        """Check if a field by the given name exists"""

    def keys():
        """Return the names of the fields present
        on this schema"""

    def searchable():
        """Return a list containing names of all
        the fields present on this schema that are
        searchable.
        """

class ISchema(ISchemata):
    """ Schema """

    def edit(instance, name, value):
        """Call the mutator by name on instance,
        setting the value.
        """

    def setDefaults(instance):
        """Only call during object initialization.

        Sets fields to schema defaults.
        """

    def updateAll(instance, **kwargs):
        """This method mutates fields in the given instance.

        For each keyword argument k, the key indicates the name of the
        field to mutate while the value is used to call the mutator.

        E.g. updateAll(instance, id='123', amount=500) will, depending on the
        actual mutators set, result in two calls: ``instance.setId('123')`` and
        ``instance.setAmount(500)``.
        """

    def allow(name):
        """Check if a field by the given name exists"""

    def validate(instance=None, REQUEST=None,
                 errors=None, data=None, metadata=None):
        """Validate the state of the entire object.

        The passed dictionary ``errors`` will be filled with human readable
        error messages as values and the corresponding fields' names as
        keys.
        """

    def toString():
        """Utility method for converting a Schema to a string for the
        purpose of comparing schema.

        This is used for determining whether a schema
        has changed in the auto update function.
        """

    def signature():
        """Return an md5 sum of the the schema.

        This is used for determining whether a schema
        has changed in the auto update function.
        """

    def changeSchemataForField(fieldname, schemataname):
        """Change the schemata for a field """

    def getSchemataNames():
        """Return list of schemata names in order of appearing"""

    def getSchemataFields(name):
        """Return list of fields belong to schema 'name'
        in order of appearing
        """

    def replaceField(name, field):
        """Replace field under ``name`` with ``field``"""

    def moveField(name, direction=None, pos=None, after=None, before=None):
        """Move a field

        name:
            name of the field
        direction:
            Move a field inside its schemata to the left (-1) or to the right (+1)
        pos:
            Moves a field to a position in the whole schema. pos is either a number
            or 'top' or 'bottom'
        after:
            Moves the field 'name' after the field 'after'
        before:
            Moves the field 'name' before the field 'before'

        """

class ICompositeSchema(ISchema):
    """A composite schema that delegates to underlying ones"""

    def getSchemas():
        """Return a list of underlying schemas in order"""

    def addSchemas(schemas):
        """Append schemas to composite"""

class IBindableSchema(ISchema):
    """A Schema that can be bound to a context object"""

    def bind(context):
        """Bind schema to context"""

class IManagedSchema(ISchema):
    """A schema that can be managed (ordering schemata,
    ordering fields, moving fields between schematas)
    """

    def delSchemata(name):
        """Remove all fields belonging to schemata 'name'"""

    def addSchemata(name):
        """Create a new schema by adding a new field with schemata 'name' """

    def moveSchemata(name, direction):
        """Move a schemata to left (direction=-1) or to right
        (direction=1)
        """

class IMultiPageSchema(Interface):
    """A marker interface for schemas which have to be loaded on seperate
    HTML pages instead of beeing displayed on one page. This should only be
    used in wizard like cases where one schema depends on the values in a
    previous one.
    """
    pass
