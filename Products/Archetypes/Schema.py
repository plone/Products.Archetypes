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


class Schema(UserDict, DefaultLayerContainer):
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
        
        self.order_fields = None
        self.index = 0
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


    def fields(self):
        """list all the fields in order"""
        if self.order_fields is None:
            f = self.values()
            f.sort(index_sort)
            self.order_fields = f

        return self.order_fields


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
    
        

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'edit')
    def edit(self, instance, name, value):
        if self.allow(name):
            instance[name] = value

    def setDefaults(self, instance):
        """Only call during object initalization. Sets fields to
        schema defaults
        """
        ## XXX think about layout/vs dyn defaults
        instance = aq_base(instance)
        for field in self.values():
            if not getattr(instance, field.name, None):
                default = field.default
                #See if the instance has a method named the default
                ##default = getattr(instance, default, default)
                ###if it does call it
                ##if callable(default):
                ##    default = default()

                field.set(instance, default)
                
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'updateAll')
    def updateAll(self, instance, **kwargs):
        keys = kwargs.keys()
        for field in self.values():
            if 'w' not in field.mode:
                log("tried to update %s:%s which is not writeable" % \
                    (instance.portal_type, field.name))
                continue
            
            method = getattr(instance, field.mutator, None)
            if not method:
                log("No method %s on %s" % (field.mutator, instance))
                continue

            if field.name in keys:
                method(kwargs[field.name])
            
    def addField(self, field):
        if IField.isImplementedBy(field):
            self[field.name] = field
            field._index = self.index
            self.index +=1

    security.declarePublic("allow")
    def allow(self, key):
        """Allow update to keys of this name (must be a valid field)"""
        return self.get(key) != None

    security.declarePublic('validate')
    def validate(self, instance, REQUEST=None, errors=None):
        """Validate the state of the entire object"""
        for name, field in self.items():
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
                        accessor = getattr(instance, self.accessor)
                        unit = accessor()
                        if hasattr(unit, 'isUnit'): ##XXX to implements
                            if unit.filename != '':
                                value = unit.filename #doesn't matter what it is
                    except:
                        pass
                if not value and isinstance(value, FileUpload) and value.filename!='':
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

            #VOCABILARY CHECKS
            if error == 0  and field.enforceVocabulary == 1:
                if value: ## we need to check this as optional field will be
                          ## empty and thats ok
                    values = field.multiValued == 1  and value or [value]
                    for value in values:
                        if not value in field.Vocabulary(instance):
                            errors[name] = "Value %s is not allowed for vocabulary " \
                                           "of element: %s" %(value, capitalize(name))
                            error = 1
                            break

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

    security.declarePublic('searchable')
    def searchable(self):
        """return the names of all the searchable fields"""
        return [f.name for f in self.values() if f.searchable]

    #ILayerRuntime
    def initalizeLayers(self, instance):
        # scan each field looking for registered layers
        # optionally call its initalizeInstance method and
        # then the initalizeField method
        initalizedLayers = []
        called = lambda x: x in initalizedLayers

        for field in self.fields():
            layers = field.registeredLayers()
            for layer, object in layers:
                if ILayer.isImplementedBy(object):
                    if not called(layer):
                        object.initalizeInstance(instance)
                        initalizedLayers.append(layer)
                    object.initalizeField(instance, field)

                    


        #Now do the same for objects registered at this level
        for layer, object in self.registeredLayers():
            if not called(layer) and ILayer.isImplementedBy(object):
                object.initalizeInstance(instance)
                initalizedLayers.append(layer)

    def cleanupLayers(self, instance):
        # scan each field looking for registered layers
        # optionally call its cleanupInstance method and
        # then the cleanupField method
        queuedLayers = []
        queued = lambda x: x in queuedLayers
        
        for field in self.fields():
            layers = field.registeredLayers()
            for layer, object in layers:
                if ILayer.isImplementedBy(object):
                    object.cleanupField(instance, field)
                    if not queued((layer, object)):
                        queuedLayers.append((layer, object))

        for layer, object in queuedLayers:
            object.cleanupInstance(instance)
                    
        #Now do the same for objects registered at this level
        for layer, object in self.registeredLayers():
            if not queued((layer, object)) and ILayer.isImplementedBy(object):
                object.cleanupInstance(instance)
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
        if 'm' not in field.generateMode:
            field.generateMode = 'mVc'
        
        FieldList.addField(self, field)


InitializeClass(Schema)

FieldList = Schema
MetadataFieldList = MetadataSchema
