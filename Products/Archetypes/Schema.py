from __future__ import nested_scopes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from utils import capitalize, DisplayList
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
from Products.validation import validation

# Used in fields() method
def index_sort(a, b): return  a._index - b._index

def getNames(schema):
    return [f.name for f in schema.fields()]

def getSchemata(klass):
    schema = klass.schema
    schemata = {}
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
        self.name = name
        UserDict.__init__(self)

        if fields is not None:
            if type(fields) not in [ListType, TupleType]:
                fields = (fields, )
                
            for field in fields:
                self.addField(field)

    security.declarePublic('getName')
    def getName(self):
        return self.name
    
    def __add__(self, other):
        c = Schemata()
        #We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)
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
            widgets[f.name] = f.widget
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
                if hasattr(field, k):
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
            self[field.name] = field
            field._index = self.index
            self.index +=1
        else:
            log_exc('Object doesnt implements IField: %s' % field)

    security.declarePublic('searchable')
    def searchable(self):
        """return the names of all the searchable fields"""
        return [f.name for f in self.values() if f.searchable]

class Schema(Schemata, UserDict, DefaultLayerContainer):
    """Manage a list of fields and run methods over them"""

    __implements__ = (ILayerRuntime, ILayerContainer)
    
    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'marshal' : None
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
        #We can't use update and keep the order so we do it manually
        for field in self.fields():
            c.addField(field)
        for field in other.fields():
            c.addField(field)
        return c

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'edit')
    def edit(self, instance, name, value):
        if self.allow(name):
            instance[name] = value

    def setDefaults(self, instance):
        """Only call during object initalization. Sets fields to
        schema defaults
        """
        ## XXX think about layout/vs dyn defaults
        for field in self.values():
            if field.name.lower() != 'id':
                # always set defaults
                #if not hasattr(aq_base(instance), field.name) and \
                #   getattr(instance, field.name, None):
                default = field.default
                #See if the instance has a method named the default
                ##default = getattr(instance, default, default)
                #if it does call it
                ##if callable(default):
                ##    default = default()
            
                field.set(instance, default)
                
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'updateAll')
    def updateAll(self, instance, **kwargs):
        keys = kwargs.keys()
        for field in self.values():
            if field.name not in keys:
                continue

            if 'w' not in field.mode:
                log("tried to update %s:%s which is not writeable" % \
                    (instance.portal_type, field.name))
                continue
            
            method = getattr(instance, field.mutator, None)
            if not method:
                log("No method %s on %s" % (field.mutator, instance))
                continue

            method(kwargs[field.name])
            
    security.declarePublic("allow")
    def allow(self, key):
        """Allow update to keys of this name (must be a valid field)"""
        return self.get(key) != None

    security.declarePublic('validate')
    def validate(self, instance, REQUEST=None, errors=None, data=None, metadata=None):
        """Validate the state of the entire object"""
        fields = []
        if data:
            fields.extend([(field.name, field) for field in self.filterFields(isMetadata=0)])
        if metadata:
            fields.extend([(field.name, field) for field in self.filterFields(isMetadata=1)])
        for name, field in fields:
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
                            if unit.filename != '':
                                value = unit.filename #doesn't matter what it is
                        elif hasattr(aq_base(unit), 'getSize') and \
                             unit.getSize():
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
                    if isinstance(value, type('')) or isinstance(value, type(u'')):
                        values = [value]
                    elif not (isinstance(value, type((1,))) or isinstance(value, type([]))):
                        raise TypeError("Field value type error")
#                    values = field.multiValued == 1  and value or [value]
                    vocab = field.Vocabulary(instance)
                    for value in values:
                        error = 1 
                        for v in vocab:
                            if type(v) in [type(()), type([])]:
                                valid = v[0]
                            else:
                                valid = v
                            if value == valid or str(value) == str(valid):
                                error = 0
                                break

                    if error == 1:
                        errors[name] = "Value %s is not allowed for vocabulary " \
                                       "of element: %s" %(value, capitalize(name))

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
    def initalizeLayers(self, instance, item=None, container=None):
        # scan each field looking for registered layers
        # optionally call its initalizeInstance method and
        # then the initalizeField method
        initalizedLayers = []
        called = lambda x: x in initalizedLayers

        for field in self.fields():
            if ILayerContainer.isImplementedBy(field):
                layers = field.registeredLayers()
                for layer, object in layers:
                    if ILayer.isImplementedBy(object):
                        if not called((layer, object)):
                            object.initalizeInstance(instance, item, container)
                            # Some layers may have the same name, but different classes,
                            # so, they may still need to be initialized
                            initalizedLayers.append((layer, object))
                        object.initalizeField(instance, field)
                        

        #Now do the same for objects registered at this level
        if ILayerContainer.isImplementedBy(self):
            for layer, object in self.registeredLayers():
                if not called((layer, object)) \
                   and ILayer.isImplementedBy(object):
                    object.initalizeInstance(instance, item, container)
                    initalizedLayers.append((layer, object))

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
                    cleanedLayers.append((layer, object))

#Reusable instance for MetadataFieldList
MDS = MetadataStorage()
                
class MetadataSchema(Schema):
    def addField(self, field):
        """Strictly enforce the contract that metadata is stored w/o
        markup and make sure each field is marked as such for
        generation and introspcection purposes.
        """
        field.isMetadata = 1
        field.storage = MDS
        field.schemata = 'metadata'
        if 'm' not in field.generateMode:
            field.generateMode = 'mVc'
        
        FieldList.addField(self, field)


InitializeClass(Schema)

FieldList = Schema
MetadataFieldList = MetadataSchema
