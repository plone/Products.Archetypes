from __future__ import nested_scopes
from types import ListType, TupleType, StringType

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
from Products.Archetypes.lib.logging import warn
from Products.Archetypes.exceptions import SchemaException
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.schemata.schemata import Schemata
from Products.Archetypes.schemata.schemata import SchemaLayerContainer

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, Explicit
from ExtensionClass import Base
from Globals import InitializeClass
from Products.CMFCore import CMFCorePermissions

__docformat__ = 'reStructuredText'


class BasicSchema(Schemata):
    """Manage a list of fields and run methods over them."""

    __implements__ = ISchema

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
                warn(msg, level=level)
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

    security.declareProtected(CMFCorePermissions.View, 'copy')
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

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'edit')
    def edit(self, instance, name, value):
        if self.allow(name):
            instance[name] = value

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setDefaults')
    def setDefaults(self, instance):
        """Only call during object initialization. Sets fields to
        schema defaults
        """
        ## XXX think about layout/vs dyn defaults
        for field in self.values():
            if field.getName().lower() == 'id': continue
            if field.type == "reference": continue

            # always set defaults on writable fields
            mutator = field.getMutator(instance)
            if mutator is None:
                continue
            default = field.getDefault(instance)

            args = (default,)
            kw = {'field': field.__name__}
            if shasattr(field, 'default_content_type'):
                # specify a mimetype if the mutator takes a
                # mimetype argument
                kw['mimetype'] = field.default_content_type
            mapply(mutator, *args, **kw)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
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

        for field in self.values():
            if field.getName() not in keys:
                continue

            if 'w' not in field.mode:
                log("tried to update %s:%s which is not writeable" % \
                    (instance.portal_type, field.getName()))
                continue

            method = field.getMutator(instance)
            if not method:
                log("No method %s on %s" % (field.mutator, instance))
                continue

            method(kwargs[field.getName()])

    security.declareProtected(CMFCorePermissions.View,
                              'allow')

    def allow(self, name):
        return self.has_key(name)

    security.declareProtected(CMFCorePermissions.View,
                              'validate')
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
        for name, field in fields:
            error = 0
            value = None
            widget = field.widget
            if form:
                result = widget.process_form(instance, field, form,
                                             empty_marker=_marker)
            else:
                result = None
            if result is None or result is _marker:
                accessor = field.getEditAccessor(instance) or field.getAccessor(instance)
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
    # XXX FIXME!
    security.declareProtected(CMFCorePermissions.View,
                              'toString')
    def toString(self):
        s = '%s: {' % self.__class__.__name__
        for f in self.fields():
            s = s + '%s,' % (f.toString())
        s = s + '}'
        return s

    security.declareProtected(CMFCorePermissions.View,
                              'signature')
    def signature(self):
        from md5 import md5
        return md5(self.toString()).digest()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'changeSchemataForField')
    def changeSchemataForField(self, fieldname, schemataname):
        """ change the schemata for a field """
        field = self[fieldname]
        self.delField(fieldname)
        field.schemata = schemataname
        self.addField(field)

    security.declareProtected(CMFCorePermissions.View, 'getSchemataNames')
    def getSchemataNames(self):
        """Return list of schemata names in order of appearing"""
        lst = []
        for f in self.fields():
            if not f.schemata in lst:
                lst.append(f.schemata)
        return lst

    security.declareProtected(CMFCorePermissions.View, 'getSchemataFields')
    def getSchemataFields(self, name):
        """Return list of fields belong to schema 'name'
        in order of appearing
        """
        return [f for f in self.fields() if f.schemata == name]

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'replaceField')
    def replaceField(self, name, field):
        if IField.isImplementedBy(field):
            oidx = self._names.index(name)
            new_name = field.getName()
            self._names[oidx] = new_name
            del self._fields[name]
            self._fields[new_name] = field
        else:
            raise ValueError, "Object doesn't implement IField: %r" % field

InitializeClass(BasicSchema)


class Schema(BasicSchema, SchemaLayerContainer):
    """
    Schema
    """

    __implements__ = ILayerRuntime, ILayerContainer, ISchema

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

    security.declareProtected(CMFCorePermissions.View, 'copy')
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
        layers = {}
        for k, v in self.registeredLayers():
            c.registerLayer(k, v)
        return c

    security.declareProtected(CMFCorePermissions.View, 'wrapped')
    def wrapped(self, parent):
        schema = self.copy(factory=WrappedSchema)
        return schema.__of__(parent)

InitializeClass(Schema)


class WrappedSchema(Schema, Explicit):
    """
    Wrapped Schema
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

InitializeClass(WrappedSchema)


class ManagedSchema(Schema):
    """
    Managed Schema
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    __implements__ = IManagedSchema, Schema.__implements__

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'delSchemata')
    def delSchemata(self, name):
        """Remove all fields belonging to schemata 'name'"""
        for f in self.fields():
            if f.schemata == name:
                self.delField(f.getName())

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'addSchemata')
    def addSchemata(self, name):
        """Create a new schema by adding a new field with schemata 'name' """
        from Products.Archetypes.fields import StringField

        if name in self.getSchemataNames():
            raise ValueError, "Schemata '%s' already exists" % name
        self.addField(StringField('%s_default' % name, schemata=name))

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'moveSchemata')
    def moveSchemata(self, name, direction):
        """Move a schemata to left (direction=-1) or to right
        (direction=1)
        """
        if not direction in (-1, 1):
            raise ValueError, 'Direction must be either -1 or 1'

        fields = self.fields()
        fieldnames = [f.getName() for f in fields]
        schemata_names = self.getSchemataNames()

        d = {}
        for s_name in self.getSchemataNames():
            d[s_name] = self.getSchemataFields(s_name)

        pos = schemata_names.index(name)
        if direction == -1:
            if pos > 0:
                schemata_names.remove(name)
                schemata_names.insert(pos-1, name)
        if direction == 1:
            if pos < len(schemata_names):
                schemata_names.remove(name)
                schemata_names.insert(pos+1, name)

        # remove and re-add
        self.__init__()

        for s_name in schemata_names:
            for f in fields:
                if f.schemata == s_name:
                    self.addField(f)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'moveField')
    def moveField(self, name, direction):
        """Move a field inside a schema to left
        (direction=-1) or to right (direction=1)
        """
        if not direction in (-1, 1):
            raise ValueError, "Direction must be either -1 or 1"

        fields = self.fields()
        fieldnames = [f.getName() for f in fields]
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
                lst.insert(pos-1, field)
        if direction == 1:
            if pos < len(lst):
                del lst[pos]
                lst.insert(pos+1, field)

        d[field_schemata_name] = lst

        # remove and re-add
        self.__init__()
        for s_name in schemata_names:
            for f in d[s_name]:
                self.addField(f)

InitializeClass(ManagedSchema)

class MetadataSchema(Schema):
    """Schema that enforces MetadataStorage."""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
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

 
