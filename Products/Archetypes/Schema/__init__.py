from types import ListType, TupleType, StringType
from warnings import warn

from Products.Archetypes.Storage import MetadataStorage
from Products.Archetypes.Layer import DefaultLayerContainer
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.layer import ILayerContainer, \
    ILayerRuntime, ILayer
from Products.Archetypes.interfaces.schema import ISchema, ISchemata, \
    IManagedSchema
from Products.Archetypes.utils import OrderedDict, mapply, shasattr
from Products.Archetypes.mimetype_utils import getDefaultContentType
from Products.Archetypes.exceptions import SchemaException
from Products.Archetypes.exceptions import ReferenceException

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, Explicit
from ExtensionClass import Base
from App.class_init import InitializeClass
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from zope.interface import implementer

__docformat__ = 'reStructuredText'
_marker = []


def getNames(schema):
    """Returns a list of all fieldnames in the given schema."""
    return [f.getName() for f in schema.fields()]


def getSchemata(obj):
    """Returns an ordered dictionary, which maps all Schemata names to fields
    that belong to the Schemata."""

    schema = obj.Schema()
    schemata = OrderedDict()
    for f in schema.fields():
        sub = schemata.get(f.schemata, WrappedSchemata(name=f.schemata))
        sub.addField(f)
        schemata[f.schemata] = sub.__of__(obj)

    return schemata


@implementer(ISchemata)
class Schemata(Base):
    """Manage a list of fields by grouping them together.

    Schematas are identified by their names.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, name='default', fields=None):
        """Initialize Schemata and add optional fields."""

        self.__name__ = name
        self._names = []
        self._fields = {}

        if fields is not None:
            if type(fields) not in [ListType, TupleType]:
                fields = (fields, )

            for field in fields:
                self.addField(field)

    security.declareProtected(permissions.View, 'getName')

    def getName(self):
        """Returns the Schemata's name."""
        return self.__name__

    def __add__(self, other):
        """Returns a new Schemata object that contains all fields and layers
        from ``self`` and ``other``.
        """

        c = Schemata()
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)

        return c

    security.declareProtected(permissions.View, 'copy')

    def copy(self):
        """Returns a deep copy of this Schemata.
        """
        c = Schemata()
        for field in self.fields():
            c.addField(field.copy())
        return c

    security.declareProtected(permissions.View, 'fields')

    def fields(self):
        """Returns a list of my fields in order of their indices."""
        return [self._fields[name] for name in self._names]

    security.declareProtected(permissions.View, 'values')
    values = fields

    security.declareProtected(permissions.View, 'editableFields')

    def editableFields(self, instance, visible_only=False):
        """Returns a list of editable fields for the given instance
        """
        ret = []
        portal = getToolByName(instance, 'portal_url').getPortalObject()
        for field in self.fields():
            if field.writeable(instance, debug=False) and    \
                    (not visible_only or
                        field.widget.isVisible(instance, 'edit') != 'invisible') and \
                    field.widget.testCondition(instance.aq_parent, portal, instance):
                ret.append(field)
        return ret

    security.declareProtected(permissions.View, 'viewableFields')

    def viewableFields(self, instance):
        """Returns a list of viewable fields for the given instance
        """
        return [field for field in self.fields()
                if field.checkPermission('view', instance)]

    security.declareProtected(permissions.View, 'widgets')

    def widgets(self):
        """Returns a dictionary that contains a widget for
        each field, using the field name as key."""

        widgets = {}
        for f in self.fields():
            widgets[f.getName()] = f.widget
        return widgets

    security.declareProtected(permissions.View,
                              'filterFields')

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

        results = []

        for field in self.fields():  # step through each of my fields

            # predicate failed:
            failed = [pred for pred in predicates if not pred(field)]
            if failed:
                continue

            # attribute missing:
            missing_attrs = [attr for attr in values.keys()
                             if not shasattr(field, attr)]
            if missing_attrs:
                continue

            # attribute value unequal:
            diff_values = [attr for attr in values.keys()
                           if getattr(field, attr) != values[attr]]
            if diff_values:
                continue

            results.append(field)

        return results

    def __setitem__(self, name, field):
        assert name == field.getName()
        self.addField(field)

    security.declareProtected(permissions.ModifyPortalContent,
                              'addField')

    def addField(self, field):
        """Adds a given field to my dictionary of fields."""
        field = aq_base(field)
        self._validateOnAdd(field)
        name = field.getName()
        if name not in self._names:
            self._names.append(name)
        self._fields[name] = field

    def _validateOnAdd(self, field):
        """Validates fields on adding and bootstrapping
        """
        # interface test
        if not IField.providedBy(field):
            raise ValueError, "Object doesn't implement IField: %r" % field
        name = field.getName()
        # two primary fields are forbidden
        if getattr(field, 'primary', False):
            res = self.hasPrimary()
            if res is not False and name != res.getName():
                raise SchemaException(
                    "Tried to add '%s' as primary field "
                    "but %s already has the primary field '%s'." %
                    (name, repr(self), res.getName())
                )
        for pname in ('accessor', 'edit_accessor', 'mutator'):
            res = self._checkPropertyDupe(field, pname)
            if res is not False:
                res, value = res
                raise SchemaException(
                    "Tried to add '%s' with property '%s' set "
                    "to %s but '%s' has the same value." %
                    (name, pname, repr(value), res.getName())
                )
        # Do not allowed unqualified references
        if field.type in ('reference', ):
            relationship = getattr(field, 'relationship', '')
            if type(relationship) is not StringType or len(relationship) == 0:
                raise ReferenceException(
                    "Unqualified relationship or "
                    "unsupported relationship var type in field '%s'. "
                    "The relationship qualifer must be a non empty "
                    "string." % name
                )

    def __delitem__(self, name):
        if name not in self._fields:
            raise KeyError("Schemata has no field '%s'" % name)
        del self._fields[name]
        self._names.remove(name)

    def __getitem__(self, name):
        return self._fields[name]

    security.declareProtected(permissions.View, 'get')

    def get(self, name, default=None):
        return self._fields.get(name, default)

    security.declareProtected(permissions.View, 'has_key')

    def has_key(self, name):
        return name in self._fields

    __contains__ = has_key

    security.declareProtected(permissions.View, 'keys')

    def keys(self):
        return self._names

    security.declareProtected(permissions.ModifyPortalContent,
                              'delField')
    delField = __delitem__

    security.declareProtected(permissions.ModifyPortalContent,
                              'updateField')
    updateField = addField

    security.declareProtected(permissions.View, 'searchable')

    def searchable(self):
        """Returns a list containing names of all searchable fields."""

        return [f.getName() for f in self.fields() if f.searchable]

    def hasPrimary(self):
        """Returns the first primary field or False"""
        for f in self.fields():
            if getattr(f, 'primary', False):
                return f
        return False

    def _checkPropertyDupe(self, field, propname):
        check_value = getattr(field, propname, _marker)
        # None is fine too.
        if check_value is _marker or check_value is None:
            return False
        check_name = field.getName()
        for f in self.fields():
            got = getattr(f, propname, _marker)
            if got == check_value and f.getName() != check_name:
                return f, got
        return False

InitializeClass(Schemata)


class WrappedSchemata(Schemata, Explicit):
    """
    Wrapped Schemata
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

InitializeClass(WrappedSchemata)


class SchemaLayerContainer(DefaultLayerContainer):
    """Some layer management for schemas"""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _properties = {
        'marshall': None
    }

    def __init__(self):
        DefaultLayerContainer.__init__(self)
        # Layer init work
        marshall = self._props.get('marshall')
        if marshall:
            self.registerLayer('marshall', marshall)

    # ILayerRuntime
    security.declareProtected(permissions.ModifyPortalContent,
                              'initializeLayers')

    def initializeLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers optionally
        # call its initializeInstance method and then the
        # initializeField method
        initializedLayers = []
        called = lambda x: x in initializedLayers

        for field in self.fields():
            if ILayerContainer.providedBy(field):
                layers = field.registeredLayers()
                for layer, obj in layers:
                    if ILayer.providedBy(obj):
                        if not called((layer, obj)):
                            obj.initializeInstance(instance, item, container)
                            # Some layers may have the same name, but
                            # different classes, so, they may still
                            # need to be initialized
                            initializedLayers.append((layer, obj))
                        obj.initializeField(instance, field)

        # Now do the same for objects registered at this level
        if ILayerContainer.providedBy(self):
            for layer, obj in self.registeredLayers():
                if (not called((layer, obj)) and
                        ILayer.providedBy(obj)):
                    obj.initializeInstance(instance, item, container)
                    initializedLayers.append((layer, obj))

    security.declareProtected(permissions.ModifyPortalContent,
                              'cleanupLayers')

    def cleanupLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers optionally
        # call its cleanupInstance method and then the cleanupField
        # method
        queuedLayers = []
        queued = lambda x: x in queuedLayers

        for field in self.fields():
            if ILayerContainer.providedBy(field):
                layers = field.registeredLayers()
                for layer, obj in layers:
                    if not queued((layer, obj)):
                        queuedLayers.append((layer, obj))
                    if ILayer.providedBy(obj):
                        obj.cleanupField(instance, field)

        for layer, obj in queuedLayers:
            if ILayer.providedBy(obj):
                obj.cleanupInstance(instance, item, container)

        # Now do the same for objects registered at this level

        if ILayerContainer.providedBy(self):
            for layer, obj in self.registeredLayers():
                if (not queued((layer, obj)) and
                        ILayer.providedBy(obj)):
                    obj.cleanupInstance(instance, item, container)
                    queuedLayers.append((layer, obj))

    def __add__(self, other):
        c = SchemaLayerContainer()
        layers = {}
        for k, v in self.registeredLayers():
            layers[k] = v
        for k, v in other.registeredLayers():
            layers[k] = v
        for k, v in layers.items():
            c.registerLayer(k, v)
        return c

    security.declareProtected(permissions.View, 'copy')

    def copy(self):
        c = SchemaLayerContainer()
        for k, v in self.registeredLayers():
            c.registerLayer(k, v)
        return c

InitializeClass(SchemaLayerContainer)


@implementer(ISchema)
class BasicSchema(Schemata):
    """Manage a list of fields and run methods over them."""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _properties = {}

    def __init__(self, *args, **kwargs):
        """
        Initialize a Schema.

        The first positional argument may be a sequence of
        Fields. (All further positional arguments are ignored.)

        Keyword arguments are added to my properties.
        """
        Schemata.__init__(self)

        self._props = self._properties.copy()
        self._props.update(kwargs)

        if len(args):
            if type(args[0]) in [ListType, TupleType]:
                for field in args[0]:
                    self.addField(field)
            else:
                msg = ('You are passing positional arguments '
                       'to the Schema constructor. '
                       'Please consult the docstring '
                       'for %s.BasicSchema.__init__' %
                       (self.__class__.__module__,))
                level = 3
                if self.__class__ is not BasicSchema:
                    level = 4
                warn(msg, UserWarning, stacklevel=level)
                for field in args:
                    self.addField(args[0])

    def __add__(self, other):
        c = BasicSchema()
        # We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)
        # Need to be smarter when joining layers
        # and internal props
        c._props.update(self._props)
        return c

    security.declareProtected(permissions.View, 'copy')

    def copy(self):
        """Returns a deep copy of this Schema.
        """
        c = BasicSchema()
        for field in self.fields():
            c.addField(field.copy())
        # Need to be smarter when joining layers
        # and internal props
        c._props.update(self._props)
        return c

    security.declareProtected(permissions.ModifyPortalContent, 'edit')

    def edit(self, instance, name, value):
        if self.allow(name):
            instance[name] = value

    security.declareProtected(permissions.ModifyPortalContent,
                              'setDefaults')

    def setDefaults(self, instance):
        """Only call during object initialization. Sets fields to
        schema defaults
        """
        # TODO think about layout/vs dyn defaults
        for field in self.values():
            if field.getName().lower() == 'id':
                continue
            if field.type == "reference":
                continue

            # always set defaults on writable fields
            mutator = field.getMutator(instance)
            if mutator is None:
                continue
            default = field.getDefault(instance)

            args = (default,)
            kw = {'field': field.__name__,
                  '_initializing_': True}
            if shasattr(field, 'default_content_type'):
                # specify a mimetype if the mutator takes a
                # mimetype argument
                # if the schema supplies a default, we honour that,
                # otherwise we use the site property
                default_content_type = field.default_content_type
                if default_content_type is None:
                    default_content_type = getDefaultContentType(instance)
                kw['mimetype'] = default_content_type
            mapply(mutator, *args, **kw)

    security.declareProtected(permissions.ModifyPortalContent,
                              'updateAll')

    def updateAll(self, instance, **kwargs):
        """This method mutates fields in the given instance.

        For each keyword argument k, the key indicates the name of the
        field to mutate while the value is used to call the mutator.

        E.g. updateAll(instance, id='123', amount=500) will, depending on the
        actual mutators set, result in two calls: ``instance.setId('123')`` and
        ``instance.setAmount(500)``.
        """

        keys = kwargs.keys()

        for name in keys:

            field = self.get(name, None)

            if field is None:
                continue

            if not field.writeable(instance):
                continue

            # If passed the test above, mutator is guaranteed to
            # exist.
            method = field.getMutator(instance)
            method(kwargs[name])

    security.declareProtected(permissions.View, 'allow')

    def allow(self, name):
        return name in self

    security.declareProtected(permissions.View, 'validate')

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
            fieldsets = REQUEST.form.get('fieldsets', None)
        else:
            fieldset = fieldsets = None
        fields = []

        if fieldsets is not None:
            schemata = instance.Schemata()
            for fieldset in fieldsets:
                fields += [(field.getName(), field)
                           for field in schemata[fieldset].fields()]
        elif fieldset is not None:
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

        for name, field in fields:

            # Should not validate something we can't write to anyway
            if not field.writeable(instance):
                continue

            value = None
            widget = field.widget

            if widget.isVisible(instance, 'edit') != 'visible':
                continue

            if form:
                result = widget.process_form(instance, field, form,
                                             empty_marker=_marker)
            else:
                result = None
            if result is None or result is _marker:
                accessor = field.getEditAccessor(
                    instance) or field.getAccessor(instance)
                if accessor is not None:
                    value = accessor()
                else:
                    # can't get value to validate -- bail
                    continue
            else:
                value = result[0]

            res = field.validate(instance=instance,
                                 value=value,
                                 errors=errors,
                                 REQUEST=REQUEST)
            if res:
                errors[field.getName()] = res
        return errors

    # Utility method for converting a Schema to a string for the
    # purpose of comparing schema.  This comparison is used for
    # determining whether a schema has changed in the auto update
    # function.  Right now it's pretty crude.
    # TODO FIXME!
    security.declareProtected(permissions.View,
                              'toString')

    def toString(self):
        s = '%s: {' % self.__class__.__name__
        for f in self.fields():
            s = s + '%s,' % (f.toString())
        s = s + '}'
        return s

    security.declareProtected(permissions.View,
                              'signature')

    def signature(self):
        try:
            from hashlib import md5
        except:
            from md5 import md5
        return md5(self.toString()).digest()

    security.declareProtected(permissions.ModifyPortalContent,
                              'changeSchemataForField')

    def changeSchemataForField(self, fieldname, schemataname):
        """ change the schemata for a field """
        field = self[fieldname]
        self.delField(fieldname)
        field.schemata = schemataname
        self.addField(field)

    security.declareProtected(permissions.View, 'getSchemataNames')

    def getSchemataNames(self):
        """Return list of schemata names in order of appearing"""
        lst = []
        for f in self.fields():
            if not f.schemata in lst:
                lst.append(f.schemata)
        return lst

    security.declareProtected(permissions.View, 'getSchemataFields')

    def getSchemataFields(self, name):
        """Return list of fields belong to schema 'name'
        in order of appearing
        """
        return [f for f in self.fields() if f.schemata == name]

    security.declareProtected(permissions.ModifyPortalContent,
                              'replaceField')

    def replaceField(self, name, field):
        if IField.providedBy(field):
            oidx = self._names.index(name)
            new_name = field.getName()
            self._names[oidx] = new_name
            del self._fields[name]
            self._fields[new_name] = field
        else:
            raise ValueError, "Object doesn't implement IField: %r" % field

InitializeClass(BasicSchema)


@implementer(ILayerRuntime, ILayerContainer, ISchema)
class Schema(BasicSchema, SchemaLayerContainer):
    """
    Schema
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, *args, **kwargs):
        BasicSchema.__init__(self, *args, **kwargs)
        SchemaLayerContainer.__init__(self)

    def __add__(self, other):
        c = Schema()
        # We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)
        # Need to be smarter when joining layers
        # and internal props
        c._props.update(self._props)
        layers = {}
        for k, v in self.registeredLayers():
            layers[k] = v
        for k, v in other.registeredLayers():
            layers[k] = v
        for k, v in layers.items():
            c.registerLayer(k, v)
        return c

    security.declareProtected(permissions.View, 'copy')

    def copy(self, factory=None):
        """Returns a deep copy of this Schema.
        """
        if factory is None:
            factory = self.__class__
        c = factory()
        for field in self.fields():
            c.addField(field.copy())
        # Need to be smarter when joining layers
        # and internal props
        c._props.update(self._props)
        for k, v in self.registeredLayers():
            c.registerLayer(k, v)
        return c

    security.declareProtected(permissions.View, 'wrapped')

    def wrapped(self, parent):
        schema = self.copy(factory=WrappedSchema)
        return schema.__of__(parent)

    security.declareProtected(permissions.ModifyPortalContent,
                              'moveField')

    def moveField(self, name, direction=None, pos=None, after=None, before=None):
        """Move a field

        >>> from Products.Archetypes.atapi import StringField as SF
        >>> schema = Schema((SF('a'), SF('b'), SF('c'),))

        >>> schema.keys()
        ['a', 'b', 'c']

        >>> sbefore = schema.copy()
        >>> sbefore.moveField('c', before='a')
        >>> sbefore.keys()
        ['c', 'a', 'b']

        >>> safter = schema.copy()
        >>> safter.moveField('a', after='b')
        >>> safter.keys()
        ['b', 'a', 'c']

        >>> spos = schema.copy()
        >>> spos.moveField('b', pos='top')
        >>> spos.keys()
        ['b', 'a', 'c']

        >>> spos = schema.copy()
        >>> spos.moveField('b', pos='bottom')
        >>> spos.keys()
        ['a', 'c', 'b']

        >>> spos = schema.copy()
        >>> spos.moveField('c', pos=0)
        >>> spos.keys()
        ['c', 'a', 'b']

        maxint can be used to move the field to the last position possible
        >>> from sys import maxint
        >>> spos = schema.copy()
        >>> spos.moveField('a', pos=maxint)
        >>> spos.keys()
        ['b', 'c', 'a']

        Errors
        ======

        >>> schema.moveField('d', pos=0)
        Traceback (most recent call last):
        ...
        KeyError: 'd'

        >>> schema.moveField('a', pos=0, before='b')
        Traceback (most recent call last):
        ...
        ValueError: You must apply exactly one argument.

        >>> schema.moveField('a')
        Traceback (most recent call last):
        ...
        ValueError: You must apply exactly one argument.

        >>> schema.moveField('a', before='a')
        Traceback (most recent call last):
        ...
        ValueError: name and before can't be the same

        >>> schema.moveField('a', after='a')
        Traceback (most recent call last):
        ...
        ValueError: name and after can't be the same

        >>> schema.moveField('a', pos='foo')
        Traceback (most recent call last):
        ...
        ValueError: pos must be a number or top/bottom

        """
        if bool(direction) + bool(after) + bool(before) + bool(pos is not None) != 1:
            raise ValueError, "You must apply exactly one argument."
        keys = self.keys()

        if name not in keys:
            raise KeyError, name

        if direction is not None:
            return self._moveFieldInSchemata(name, direction)

        if pos is not None:
            if not (isinstance(pos, int) or pos in ('top', 'bottom',)):
                raise ValueError, "pos must be a number or top/bottom"
            if pos == 'top':
                return self._moveFieldToPosition(name, 0)
            elif pos == 'bottom':
                return self._moveFieldToPosition(name, len(keys))
            else:
                return self._moveFieldToPosition(name, pos)

        if after is not None:
            if after == name:
                raise ValueError, "name and after can't be the same"
            idx = keys.index(after)
            return self._moveFieldToPosition(name, idx + 1)

        if before is not None:
            if before == name:
                raise ValueError, "name and before can't be the same"
            idx = keys.index(before)
            return self._moveFieldToPosition(name, idx)

    def _moveFieldToPosition(self, name, pos):
        """Moves a field with the name 'name' to the position 'pos'

        This method doesn't obey the assignement of fields to a schemata
        """
        keys = self._names
        oldpos = keys.index(name)
        keys.remove(name)
        if oldpos >= pos:
            keys.insert(pos, name)
        else:
            keys.insert(pos - 1, name)
        self._names = keys

    def _moveFieldInSchemata(self, name, direction):
        """Moves a field with the name 'name' inside its schemata
        """
        if not direction in (-1, 1):
            raise ValueError, "Direction must be either -1 or 1"

        schemata_names = self.getSchemataNames()

        field = self[name]
        field_schemata_name = self[name].schemata

        d = {}
        for s_name in self.getSchemataNames():
            d[s_name] = self.getSchemataFields(s_name)

        lst = d[field_schemata_name]  # list of fields of schemata
        pos = [f.getName() for f in lst].index(field.getName())

        if direction == -1:
            if pos > 0:
                del lst[pos]
                lst.insert(pos - 1, field)
        if direction == 1:
            if pos < len(lst):
                del lst[pos]
                lst.insert(pos + 1, field)

        d[field_schemata_name] = lst

        # remove and re-add
        self.__init__()
        for s_name in schemata_names:
            for f in d[s_name]:
                self.addField(f)


InitializeClass(Schema)


class WrappedSchema(Schema, Explicit):
    """
    Wrapped Schema
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

InitializeClass(WrappedSchema)


@implementer(IManagedSchema)
class ManagedSchema(Schema):
    """
    Managed Schema
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    security.declareProtected(permissions.ModifyPortalContent,
                              'delSchemata')

    def delSchemata(self, name):
        """Remove all fields belonging to schemata 'name'"""
        for f in self.fields():
            if f.schemata == name:
                self.delField(f.getName())

    security.declareProtected(permissions.ModifyPortalContent,
                              'addSchemata')

    def addSchemata(self, name):
        """Create a new schema by adding a new field with schemata 'name' """
        from Products.Archetypes.Field import StringField

        if name in self.getSchemataNames():
            raise ValueError, "Schemata '%s' already exists" % name
        self.addField(StringField('%s_default' % name, schemata=name))

    security.declareProtected(permissions.ModifyPortalContent,
                              'moveSchemata')

    def moveSchemata(self, name, direction):
        """Move a schemata to left (direction=-1) or to right
        (direction=1)
        """
        if not direction in (-1, 1):
            raise ValueError, 'Direction must be either -1 or 1'

        fields = self.fields()
        schemata_names = self.getSchemataNames()

        d = {}
        for s_name in self.getSchemataNames():
            d[s_name] = self.getSchemataFields(s_name)

        pos = schemata_names.index(name)
        if direction == -1:
            if pos > 0:
                schemata_names.remove(name)
                schemata_names.insert(pos - 1, name)
        if direction == 1:
            if pos < len(schemata_names):
                schemata_names.remove(name)
                schemata_names.insert(pos + 1, name)

        # remove and re-add
        self.__init__()

        for s_name in schemata_names:
            for f in fields:
                if f.schemata == s_name:
                    self.addField(f)

InitializeClass(ManagedSchema)


# Reusable instance for MetadataFieldList
MDS = MetadataStorage()


class MetadataSchema(Schema):
    """Schema that enforces MetadataStorage."""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    security.declareProtected(permissions.ModifyPortalContent,
                              'addField')

    def addField(self, field):
        """Strictly enforce the contract that metadata is stored w/o
        markup and make sure each field is marked as such for
        generation and introspcection purposes.
        """
        _properties = {'isMetadata': 1,
                       'storage': MetadataStorage(),
                       'schemata': 'metadata',
                       'generateMode': 'mVc'}

        field.__dict__.update(_properties)
        field.registerLayer('storage', field.storage)

        Schema.addField(self, field)

InitializeClass(MetadataSchema)


FieldList = Schema
MetadataFieldList = MetadataSchema
