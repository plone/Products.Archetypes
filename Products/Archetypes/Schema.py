from __future__ import nested_scopes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from utils import capitalize, DisplayList, OrderedDict, mapply
from debug import log, log_exc
from ZPublisher.HTTPRequest import FileUpload
from BaseUnit import BaseUnit
from types import StringType
from Storage import AttributeStorage, MetadataStorage
from DateTime import DateTime
from Layer import DefaultLayerContainer
from interfaces.field import IField, IObjectField, IImageField
from interfaces.layer import ILayerContainer, ILayerRuntime, ILayer
from interfaces.storage import IStorage
from interfaces.base import IBaseUnit
from exceptions import ObjectFieldException
from Products.CMFCore.utils import getToolByName

__docformat__ = 'reStructuredText'

def getNames(schema):
    """Returns a list of all fieldnames in the given schema."""

    return [f.getName() for f in schema.fields()]


def getSchemata(klass):
    """Returns an ordered dictionary, which maps all Schemata names to fields
    that belong to the Schemata."""

    schema = klass.schema
    schemata = OrderedDict()
    for f in schema.fields():
        sub = schemata.get(f.schemata, Schemata(name=f.schemata))
        sub.addField(f)
        schemata[f.schemata] = sub

    return schemata


class Schemata(UserDict):
    """Manage a list of fields by grouping them together.

    Schematas are identified by their names.
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _order_fields = None # cached index-ordered list of fields

    def __init__(self, name='default', fields=None):
        """Initialize Schemata and add optional fields."""

        self.__name__ = name
        UserDict.__init__(self)

        self._index = 0

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

        *FIXME*: Why do we add layers when we're not even inheriting from
        DefaultLayerContainer?"""

        c = Schemata()
        #We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)

        #XXX This should also merge properties (last write wins)
        c._layers = self._layers.copy()
        c._layers.update(other._layers)
        return c


    security.declareProtected(CMFCorePermissions.View,
                              'copy')
    def copy(self):
        """Returns a deep copy of this Schemata.

        *FIXME*: Why does this return a Schema and not a Schemata object?"""

        c = Schema()
        for field in self.fields():
            c.addField(field.copy())
        return c


    security.declareProtected(CMFCorePermissions.View,
                              'fields')
    def fields(self):
        """Returns a list of my fields in order of their indices."""

        if self._order_fields is None:
            f = self.values()
            f.sort(lambda a, b: a._index - b._index)
            self._order_fields = f

        return self._order_fields


    security.declareProtected(CMFCorePermissions.View,
                              'widgets')
    def widgets(self):
        """Returns a dictionary that contains a widget for each field, keyed
        by field name."""

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
                             if not hasattr(field, attr)]
            if missing_attrs: continue

            # attribute value unequal:
            diff_values = [attr for attr in values.keys() \
                           if getattr(field, attr) != values[attr]]
            if diff_values: continue

            results.append(field)

        return results

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'addField')
    def addField(self, field):
        """Adds a given field to my dictionary of fields."""

        if IField.isImplementedBy(field):
            self[field.getName()] = field
            field._index = self._index
            self._index +=1
            self._order_fields = None
        else:
            log_exc('Object doesnt implement IField: %s' % field)


    security.declareProtected(CMFCorePermissions.View,
                              'searchable')
    def searchable(self):
        """Returns a list containing names of all searchable fields."""

        return [f.getName() for f in self.values() if f.searchable]



class Schema(Schemata, DefaultLayerContainer):
    """Manage a list of fields and run methods over them."""

    __implements__ = (ILayerRuntime, ILayerContainer)

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _properties = {
        'marshall' : None
        }


    def __init__(self, *args, **kwargs):
        """
        Initialize a Schema.

        The first positional argument may be a sequence of Fields which will be
        stored inside my UserDict dict. (All further positional arguments are
        ignored.)

        Keyword arguments are added to my properties.
        """
        Schemata.__init__(self)
        DefaultLayerContainer.__init__(self)

        self._props = self._properties.copy()
        self._props.update(kwargs)

        if len(args):
            if type(args[0]) in [ListType, TupleType]:
                for field in args[0]:
                    self.addField(field)
            else:
                self.addField(args[0])

        #Layer init work
        marshall = self._props.get('marshall')
        if marshall:
            self.registerLayer('marshall', marshall)

    def __add__(self, other):
        c = Schema()
        # We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)
        # Need to be smarter when joining layers
        # and internal props
        layers = {}
        for k, v in self.registeredLayers():
            layers[k] = v
        for k, v in other.registeredLayers():
            layers[k] = v
        for k, v in layers.items():
            c.registerLayer(k, v)
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
            if field.getName().lower() != 'id':
                # always set defaults on writable fields
                mutator = field.getMutator(instance)
                if mutator is None:
                    continue
                #if not hasattr(aq_base(instance), field.getName()) and \
                #   getattr(instance, field.getName(), None):
                default = field.default
                if field.default_method:
                    method = getattr(instance, field.default_method, None)
                    if method:
                        default = method()
                args = (default,)
                kw = {}
                if hasattr(field, 'default_content_type'):
                    # specify a mimetype if the mutator takes a mimetype argument
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
    def allow(self, key):
        """This returns 1 for any field that I contain, where key is the
        field's name."""

        return self.get(key) != None

    security.declareProtected(CMFCorePermissions.View,
                              'validate')
    def validate(self, instance,
                 REQUEST=None, errors=None, data=None, metadata=None):
        """Validate the state of the entire object.

        The passed dictionary ``errors`` will be filled with human readable
        error messages as values and the corresponding fields' names as
        keys.

        *FIXME*: What's data and metadata arguments?
        """
        # *TODO*: This method is approx. 130 lines long and has up to 7 nesting
        #         levels!

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

        for name, field in fields:
            if name == 'id':
                m_tool = getToolByName(instance, 'portal_membership')
                member = m_tool.getAuthenticatedMember()
                if not member.getProperty('visible_ids', None) and \
                   not (REQUEST and REQUEST.form.get('id', None)):
                    continue
            if errors and errors.has_key(name):
                continue
            error = 0
            value = None
            if REQUEST:
                form = REQUEST.form
                for postfix in ['_file', '']: ## Contract with FileWidget
                    value = form.get("%s%s" % (name, postfix), None)
                    if type(value) != type(''):
                        if isinstance(value, FileUpload):
                            if value.filename == '':
                                continue
                            else:
                                break
                        else:
                            # Do other types need special handling here?
                            pass

                    if value is not None and value != '':
                        break

            # If no REQUEST, validate existing value
            else:
                accessor = field.getAccessor(instance)
                if accessor is not None:
                    value = accessor()
                else:
                    # can't get value to validate -- bail
                    break

            # REQUIRED CHECK
            if field.required == 1:
                if not value or value == "":
                    ## The only time a field would not be resubmitted
                    ## with the form is if was a file object from a
                    ## previous edit. That will not come back.  We
                    ## have to check to see that the field is
                    ## populated in that case
                    accessor = field.getAccessor(instance)
                    if accessor is not None:
                        unit = accessor()
                        if (IBaseUnit.isImplementedBy(unit) or
                            (IImageField.isImplementedBy(field) and
                             isinstance(unit, field.image_class))):
                            if hasattr(aq_base(unit), 'get_size'):
                                if unit.filename != '' or unit.get_size():
                                    value = 1 # value doesn't matter
                                elif unit.get_size():
                                    value = unit

                if ((isinstance(value, FileUpload) and value.filename != '') or
                    (isinstance(value, FileType) and value.name != '')):
                    # OK, its a file, is it empty?
                    value.seek(-1, 2)
                    size = value.tell()
                    value.seek(0)
                    if size == 0:
                        value = None

                if not value:
                    errors[name] =  "%s is required, please correct" % capitalize(name)
                    error = 1
                    continue

            # VOCABULARY CHECKS
            if error == 0  and field.enforceVocabulary == 1:
                if value: ## we need to check this as optional field will be
                          ## empty and thats ok
                    # coerce value into a list called values
                    values = value
                    if isinstance(value, type('')) or \
                           isinstance(value, type(u'')):
                        values = [value]
                    elif not (isinstance(value, type((1,))) or \
                              isinstance(value, type([]))):
                        raise TypeError("Field value type error")
                    vocab = field.Vocabulary(instance)
                    # filter empty
                    values = [instance.unicodeEncode(v)
                              for v in values if v.strip()]
                    # extract valid values from vocabulary
                    valids = []
                    for v in vocab:
                        if type(v) in [type(()), type([])]:
                            v = v[0]
                        if not type(v) in [type(''), type(u'')]:
                            v = str(v)
                        valids.append(instance.unicodeEncode(v))
                    # check field values
                    for val in values:
                        error = 1
                        for v in valids:
                            if val == v:
                                error = 0
                                break

                    if error == 1:
                        errors[name] = ("Value %s is not allowed for vocabulary"
                                        " of element: %s") % (val,
                                                              capitalize(name))

            # Call any field level validation
            if error == 0 and value:
                try:
                    res = field.validate(value, instance=instance,
                                         field=field, REQUEST=REQUEST)
                    if res:
                        errors[name] = res
                        error = 1
                except Exception, E:
                    log_exc()
                    errors[name] = E

            # CUSTOM VALIDATORS
            if error == 0:
                try:
                    instance.validate_field(name, value, errors)
                except Exception, E:
                    log_exc()
                    errors[name] = E


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
                for layer, object in layers:
                    if ILayer.isImplementedBy(object):
                        if not called((layer, object)):
                            object.initializeInstance(instance, item, container)
                            # Some layers may have the same name, but
                            # different classes, so, they may still
                            # need to be initialized
                            initializedLayers.append((layer, object))
                        object.initializeField(instance, field)

        # Now do the same for objects registered at this level
        if ILayerContainer.isImplementedBy(self):
            for layer, object in self.registeredLayers():
                if not called((layer, object)) \
                   and ILayer.isImplementedBy(object):
                    object.initializeInstance(instance, item, container)
                    initializedLayers.append((layer, object))


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
                for layer, object in layers:
                    if not queued((layer, object)):
                        queuedLayers.append((layer, object))
                    if ILayer.isImplementedBy(object):
                        object.cleanupField(instance, field)

        for layer, object in queuedLayers:
            if ILayer.isImplementedBy(object):
                object.cleanupInstance(instance, item, container)

        # Now do the same for objects registered at this level

        if ILayerContainer.isImplementedBy(self):
            for layer, object in self.registeredLayers():
                if not queued((layer, object)) and ILayer.isImplementedBy(object):
                    object.cleanupInstance(instance, item, container)
                    queuedLayers.append((layer, object))

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

# Reusable instance for MetadataFieldList
MDS = MetadataStorage()

class MetadataSchema(Schema):
    """Schema that enforces MetadataStorage."""

    security = ClassSecurityInfo()

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


InitializeClass(Schema)
InitializeClass(Schemata)
InitializeClass(MetadataSchema)

FieldList = Schema
MetadataFieldList = MetadataSchema
