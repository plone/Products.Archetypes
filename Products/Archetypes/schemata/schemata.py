from __future__ import nested_scopes
from types import ListType, TupleType, StringType
import warnings

from Products.Archetypes.storages import MetadataStorage
from Products.Archetypes.lib.layer import DefaultLayerContainer
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces.layer import ILayerRuntime
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.schema import ISchema
from Products.Archetypes.interfaces.schema import ISchemata
from Products.Archetypes.interfaces.schema import IManagedSchema
from Products.Archetypes.lib.vocabulary import OrderedDict
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.logging import log
from Products.Archetypes.exceptions import SchemaException
from Products.Archetypes.exceptions import ReferenceException

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, Explicit
from ExtensionClass import Base
from Globals import InitializeClass
from Products.CMFCore import CMFCorePermissions

__docformat__ = 'reStructuredText'

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

class Schemata(Base):
    """Manage a list of fields by grouping them together.

    Schematas are identified by their names.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    __implements__ = ISchemata

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

    security.declareProtected(CMFCorePermissions.View,
                              'getName')
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


    security.declareProtected(CMFCorePermissions.View,
                              'copy')
    def copy(self):
        """Returns a deep copy of this Schemata.
        """
        c = Schemata()
        for field in self.fields():
            c.addField(field.copy())
        return c


    security.declareProtected(CMFCorePermissions.View,
                              'fields')
    def fields(self):
        """Returns a list of my fields in order of their indices."""
        return [self._fields[name] for name in self._names]


    security.declareProtected(CMFCorePermissions.View,
                              'values')
    values = fields

    security.declareProtected(CMFCorePermissions.View,
                              'widgets')
    def widgets(self):
        """Returns a dictionary that contains a widget for
        each field, using the field name as key."""

        widgets = {}
        for f in self.fields():
            widgets[f.getName()] = f.widget
        return widgets


    security.declareProtected(CMFCorePermissions.View,
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

        for field in self.fields(): # step through each of my fields

            # predicate failed:
            failed = [pred for pred in predicates if not pred(field)]
            if failed: continue

            # attribute missing:
            missing_attrs = [attr for attr in values.keys() \
                             if not shasattr(field, attr)]
            if missing_attrs: continue

            # attribute value unequal:
            diff_values = [attr for attr in values.keys() \
                           if getattr(field, attr) != values[attr]]
            if diff_values: continue

            results.append(field)

        return results

    def __setitem__(self, name, field):
        assert name == field.getName()
        self.addField(field)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
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
        if not IField.isImplementedBy(field):
            raise ValueError, "Object doesn't implement IField: %r" % field
        name = field.getName()
        # two primary fields are forbidden
        if getattr(field, 'primary', False):
            res = self.hasPrimary()
            if res is not False and name != res.getName():
                raise SchemaException("Tried to add '%s' as primary field "\
                         "but %s already has the primary field '%s'." % \
                         (name, repr(self), res.getName())
                      )
        # Do not allowed unqualified references
        if field.type in ('reference', ):
            relationship = getattr(field, 'relationship', '')
            if type(relationship) is not StringType or len(relationship) == 0:
                raise ReferenceException("Unqualified relationship or "\
                          "unsupported relationship var type in field '%s'. "\
                          "The relationship qualifer must be a non empty "\
                          "string." % name
                      )

    def __delitem__(self, name):
        if not self._fields.has_key(name):
            raise KeyError("Schemata has no field '%s'" % name)
        del self._fields[name]
        self._names.remove(name)

    def __getitem__(self, name):
        return self._fields[name]

    security.declareProtected(CMFCorePermissions.View,
                              'get')
    def get(self, name, default=None):
        return self._fields.get(name, default)

    security.declareProtected(CMFCorePermissions.View,
                              'has_key')
    def has_key(self, name):
        return self._fields.has_key(name)

    security.declareProtected(CMFCorePermissions.View,
                              'keys')
    def keys(self):
        return self._names

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'delField')
    delField = __delitem__

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'updateField')
    updateField = addField

    security.declareProtected(CMFCorePermissions.View,
                              'searchable')
    def searchable(self):
        """Returns a list containing names of all searchable fields."""

        return [f.getName() for f in self.fields() if f.searchable]
    
    def hasPrimary(self):
        """Returns the first primary field or False"""
        for f in self.fields():
            if getattr(f, 'primary', False):
                return f
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
        'marshall' : None
        }

    def __init__(self):
        DefaultLayerContainer.__init__(self)
        #Layer init work
        marshall = self._props.get('marshall')
        if marshall:
            self.registerLayer('marshall', marshall)

    # ILayerRuntime
    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'initializeLayers')
    def initializeLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers optionally
        # call its initializeInstance method and then the
        # initializeField method
        initializedLayers = []
        called = lambda x: x in initializedLayers

        for field in self.fields():
            if ILayerContainer.isImplementedBy(field):
                layers = field.registeredLayers()
                for layer, obj in layers:
                    if ILayer.isImplementedBy(obj):
                        if not called((layer, obj)):
                            obj.initializeInstance(instance, item, container)
                            # Some layers may have the same name, but
                            # different classes, so, they may still
                            # need to be initialized
                            initializedLayers.append((layer, obj))
                        obj.initializeField(instance, field)

        # Now do the same for objects registered at this level
        if ILayerContainer.isImplementedBy(self):
            for layer, obj in self.registeredLayers():
                if (not called((layer, obj)) and
                    ILayer.isImplementedBy(obj)):
                    obj.initializeInstance(instance, item, container)
                    initializedLayers.append((layer, obj))


    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'cleanupLayers')
    def cleanupLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers optionally
        # call its cleanupInstance method and then the cleanupField
        # method
        queuedLayers = []
        queued = lambda x: x in queuedLayers

        for field in self.fields():
            if ILayerContainer.isImplementedBy(field):
                layers = field.registeredLayers()
                for layer, obj in layers:
                    if not queued((layer, obj)):
                        queuedLayers.append((layer, obj))
                    if ILayer.isImplementedBy(obj):
                        obj.cleanupField(instance, field)

        for layer, obj in queuedLayers:
            if ILayer.isImplementedBy(obj):
                obj.cleanupInstance(instance, item, container)

        # Now do the same for objects registered at this level

        if ILayerContainer.isImplementedBy(self):
            for layer, obj in self.registeredLayers():
                if (not queued((layer, obj)) and
                    ILayer.isImplementedBy(obj)):
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

    security.declareProtected(CMFCorePermissions.View, 'copy')
    def copy(self):
        c = SchemaLayerContainer()
        layers = {}
        for k, v in self.registeredLayers():
            c.registerLayer(k, v)
        return c

InitializeClass(SchemaLayerContainer)
 
