from __future__ import nested_scopes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from utils import capitalize, DisplayList, OrderedDict
from debug import log, log_exc
from ZPublisher.HTTPRequest import FileUpload
from BaseUnit import BaseUnit
from types import StringType
from Storage import AttributeStorage, MetadataStorage
from DateTime import DateTime
from Layer import DefaultLayerContainer
from interfaces.field import IField, IObjectField
from interfaces.layer import ILayerContainer, ILayerRuntime, ILayer
from interfaces.storage import IStorage
from interfaces.base import IBaseUnit
from exceptions import ObjectFieldException
from Products.CMFCore.utils import getToolByName

# Used in fields() method
def index_sort(a, b): return  a._index - b._index

def getNames(schema):
    return [f.getName() for f in schema.fields()]

def getSchemata(klass):
    schema = klass.schema
    schemata = OrderedDict()
    for f in schema.fields():
        sub = schemata.get(f.schemata, Schemata(name=f.schemata))
        sub.addField(f)
        schemata[f.schemata] = sub
    return schemata

class Schemata(UserDict):
    """Manage a list of fields by grouping them together"""

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")
    __allow_access_to_unprotected_subobjects__ = 1

    order_fields = None
    index = 0

    def __init__(self, name='default', fields=None):
        self.__name__ = name
        UserDict.__init__(self)

        if fields is not None:
            if type(fields) not in [ListType, TupleType]:
                fields = (fields, )

            for field in fields:
                self.addField(field)

    security.declarePublic('getName')
    def getName(self):
        return self.__name__

    def __add__(self, other):
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


    def copy(self):
        c = Schema()
        for field in self.fields():
            c.addField(field.copy())
        return c


    security.declarePublic('fields')
    def fields(self):
        """list all the fields in order"""
        if self.order_fields is None:
            f = self.values()
            f.sort(index_sort)
            self.order_fields = f

        return self.order_fields

    security.declarePublic('widgets')
    def widgets(self):
        """list all the widgets in order, keyed by field name"""
        widgets = {}
        for f in self.fields():
            widgets[f.getName()] = f.widget
        return widgets

    def filterFields(self, *args, **kwargs):
        """Args is a list of callable conditions
        arg(field) -> 0, omit field, 1 keep field
        kwargs is a list of attribute -> valid value mappings
        if the field doesn't match the rhs then its ommited
        """
        results = []
        fields = self.fields()

        for field in fields:
            skip = 0
            for arg in args:
                if arg(field) == 0:
                    skip = 1
                    break

            for k, v in kwargs.items():
                if not hasattr(field, k):
                    skip = 1
                    break
                else:
                    fv = getattr(field, k)
                    if fv != v:
                        skip = 1
                        break

            if not skip:
                results.append(field)

        return results

    security.declarePrivate('addField')
    def addField(self, field):
        if IField.isImplementedBy(field):
            self[field.getName()] = field
            field._index = self.index
            self.index +=1
        else:
            log_exc('Object doesnt implements IField: %s' % field)

    security.declarePublic('searchable')
    def searchable(self):
        """return the names of all the searchable fields"""
        return [f.getName() for f in self.values() if f.searchable]

class Schema(Schemata, UserDict, DefaultLayerContainer):
    """Manage a list of fields and run methods over them"""

    __implements__ = (ILayerRuntime, ILayerContainer)

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'marshall' : None
        }

    def __init__(self, *args, **kwargs):
        UserDict.__init__(self)
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
                mutator(default)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'updateAll')
    def updateAll(self, instance, **kwargs):
        keys = kwargs.keys()

        for field in self.values():
            if field.getName() not in keys:
                continue

            if 'w' not in field.mode:
                log("tried to update %s:%s which is not writeable" % \
                    (instance.portal_type, field.getName()))
                continue

            method = getattr(instance, field.mutator, None)
            if not method:
                log("No method %s on %s" % (field.mutator, instance))
                continue

            method(kwargs[field.getName()])

    security.declarePublic("allow")
    def allow(self, key):
        """Allow update to keys of this name (must be a valid field)"""
        return self.get(key) != None

    security.declarePublic('validate')
    def validate(self, instance, REQUEST=None, errors=None, data=None, metadata=None):
        """Validate the state of the entire object"""
        if REQUEST:
            fieldset = REQUEST.form.get('fieldset', None)
        else:
            fieldset = None
        fields = []

        if fieldset is not None:
            schemata = instance.Schemata()
            fields = [(field.getName(), field) for field in schemata[fieldset].fields()]
        else:
            if data:
                fields.extend([(field.getName(), field) for field in self.filterFields(isMetadata=0)])
            if metadata:
                fields.extend([(field.getName(), field) for field in self.filterFields(isMetadata=1)])

        for name, field in fields:
            if name == 'id':
                member = getToolByName(instance, 'portal_membership').getAuthenticatedMember()
                if not member.getProperty('visible_ids', None) and \
                   not (REQUEST and REQUEST.form.get('id', None)):
                    continue
            if errors and errors.has_key(name): continue
            error = 0
            value = None
            if REQUEST:
                form = REQUEST.form
                for postfix in ['_file', '']: ##Contract with FileWidget
                    value = form.get("%s%s" % (name, postfix), None)
                    if type(value) != type(''):
                        if isinstance(value, FileUpload):
                            if value.filename == '': continue
                            else: break
                        else:
                            #Do other types need special handling here
                            pass

                    if value is not None and value != '': break

            # if no REQUEST, validate existing value
            else:
                accessor = field.getAccessor(instance)
                if accessor is not None:
                    value = accessor()
                else:
                    # can't get value to validate -- bail
                    break

            #REQUIRED CHECK
            if field.required == 1:
                if not value or value == "":
                    ## The only time a field would not be resubmitted with the form is if
                    ## was a file object from a previous edit. That will not come back.
                    ## We have to check to see that the field is populated in that case
                    try:
                        accessor = getattr(instance, field.accessor)
                        unit = accessor()
                        if IBaseUnit.isImplementedBy(unit):
                            if unit.filename != '' or unit.get_size():
                                value = 1 #value doesn't matter

                        elif hasattr(aq_base(unit), 'get_size') and \
                                 unit.get_size():
                            value = unit
                    except:
                        pass
                if ((isinstance(value, FileUpload) and value.filename != '') or
                    (isinstance(value, FileType) and value.name != '')):
                    #OK, its a file, is it empty?
                    value.seek(-1, 2)
                    size = value.tell()
                    value.seek(0)
                    if size == 0:
                        value = None

                if not value:
                    errors[name] =  "%s is required, please correct" % capitalize(name)
                    error = 1
                    break

            #VOCABULARY CHECKS
            if error == 0  and field.enforceVocabulary == 1:
                if value: ## we need to check this as optional field will be
                          ## empty and thats ok
                    # coerce value into a list called values
                    values = value
                    if isinstance(value, type('')) or isinstance(value, type(u'')):
                        values = [value]
                    elif not (isinstance(value, type((1,))) or isinstance(value, type([]))):
                        raise TypeError("Field value type error")
                    vocab = field.Vocabulary(instance)
                    # filter empty
                    values = [v for v in values if v.strip()]
                    for val in values:
                        error = 1
                        for v in vocab:
                            if type(v) in [type(()), type([])]:
                                valid = v[0]
                            else:
                                valid = v
                            # XXX do we need to do unicode casting here?
                            if val == valid or str(val) == str(valid):
                                error = 0
                                break

                    if error == 1:
                        errors[name] = "Value %s is not allowed for vocabulary " \
                                       "of element: %s" %(val, capitalize(name))

            #Call any field level validation
            if error == 0 and value:
                try:
                    res = field.validate(value)
                    if res:
                        errors[name] = res
                        error = 1
                except Exception, E:
                    log_exc()
                    errors[name] = E

            #CUSTOM VALIDATORS
            if error == 0:
                try:
                    instance.validate_field(name, value, errors)
                except Exception, E:
                    log_exc()
                    errors[name] = E

    #ILayerRuntime
    def initializeLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers
        # optionally call its initializeInstance method and
        # then the initializeField method
        initializedLayers = []
        called = lambda x: x in initializedLayers

        for field in self.fields():
            if ILayerContainer.isImplementedBy(field):
                layers = field.registeredLayers()
                for layer, object in layers:
                    if ILayer.isImplementedBy(object):
                        if not called((layer, object)):
                            object.initializeInstance(instance, item, container)
                            # Some layers may have the same name, but different classes,
                            # so, they may still need to be initialized
                            initializedLayers.append((layer, object))
                        object.initializeField(instance, field)

        #Now do the same for objects registered at this level
        if ILayerContainer.isImplementedBy(self):
            for layer, object in self.registeredLayers():
                if not called((layer, object)) \
                   and ILayer.isImplementedBy(object):
                    object.initializeInstance(instance, item, container)
                    initializedLayers.append((layer, object))

    def cleanupLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers
        # optionally call its cleanupInstance method and
        # then the cleanupField method
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

        #Now do the same for objects registered at this level

        if ILayerContainer.isImplementedBy(self):
            for layer, object in self.registeredLayers():
                if not queued((layer, object)) and ILayer.isImplementedBy(object):
                    object.cleanupInstance(instance, item, container)
                    queuedLayers.append((layer, object))

    # Utility method for converting a Schema to a string for the purpose of
    # comparing schema.  This comparison is used for determining whether a
    # schema has changed in the auto update function.  Right now it's pretty
    # crude.  XXX fixme
    def toString(self):
        s = '%s: {' % self.__class__.__name__
        for f in self.fields():
            s = s + '%s,' % (f.toString())
        s = s + '}'
        return s
    
    def signature(self):
        from md5 import md5
        return md5(self.toString()).digest()
    
    def hasI18NContent(self):
        """return true it the schema contains at least one I18N field"""
        for field in self.values():
            if field.hasI18NContent():
                return 1
        return 0


#Reusable instance for MetadataFieldList
MDS = MetadataStorage()

class MetadataSchema(Schema):
    """ Schema that enforces MetadataStorage """

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

FieldList = Schema
MetadataFieldList = MetadataSchema
