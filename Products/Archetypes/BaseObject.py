from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base, aq_acquire
from Globals import InitializeClass
from OFS.ObjectManager import ObjectManager
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from ZPublisher.HTTPRequest import FileUpload
from debug import log, log_exc
from types import FileType
import operator

from Schema import Schema
from Field import StringField
from Widget import IdWidget, StringWidget
from utils import DisplayList
from interfaces.base import IBaseObject

from Renderer import renderer

content_type = Schema((
    StringField('id',
                required=1,
                mode="rw",
                accessor="getId",
                mutator="setId",
                default=None,
                widget=IdWidget(),
                ),
    
    StringField('title',
                required=1,
                searchable=1,
                default='',
                accessor='Title',
                widget=StringWidget(),
                ),
    ))

class BaseObject(Implicit):
    security = ClassSecurityInfo()

    schema = type = content_type
    installMode = ['type', 'actions', 'navigation', 'validation', 'indexes']
    
    __implements__ = IBaseObject

    def __init__(self, oid, **kwargs):
        self.id = oid
    
    def initalizeArchetype(self, **kwargs):
        """called by the generated addXXX factory in types tool"""
        self.initalizeLayers()
        self.setDefaults()
        if kwargs:
            self.update(**kwargs)

    
    def manage_afterAdd(self, item, container):
        self.initalizeLayers()
        
    def manage_afterClone(self, item):
        pass

    def manage_beforeDelete(self, item, container):
        # should provide a hook for removing object
        # from database. Eg: when we are using
        # SQLStorage for a field.
        self.cleanupLayers()

    def initalizeLayers(self):
        self.Schema().initalizeLayers(self)

    def cleanupLayers(self):
        self.Schema().cleanupLayers(self)

    security.declarePublic("getId")
    def getId(self):
        """get the objects id"""
        return self.id

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setId')
    def setId(self, value):
        if value != self.getId():
            if hasattr(self, 'aq_parent'):
                parent = self.aq_parent
                parent.manage_renameObjects((self.id,), (value,),\
                                            getattr(self, 'REQUEST', None))
        self.id = value
    
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'getField')
    def getField(self, key):
        return self.Schema().get(key)

    security.declareProtected(CMFCorePermissions.View, 'getDefault')
    def getDefault(self, field):
        """return the default from the type info"""
        field = self.getField(field)
        return field.default

 
    security.declareProtected(CMFCorePermissions.View, 'isBinary')
    def isBinary(self, key):
        element = getattr(self, key, None)
        if element and hasattr(aq_base(element), 'isBinary'):
            return element.isBinary()
        return 0

    security.declareProtected(CMFCorePermissions.View, 'widget')
    def widget(self, field_name, mode="view", **kwargs):
        try:
            widget = self.Schema()[field_name].widget
            return renderer.render(field_name, mode, widget, self,
                                   **kwargs)
        except Exception, E:
            return "%s:%s -> %s" % (self.portal_type, field_name, E)


    security.declareProtected(CMFCorePermissions.View, 'getContentType')
    def getContentType(self, key):
        value = 'text/plain' #this should maybe be octet stream or something?
        element = getattr(self, key, None)
        if element and hasattr(element, 'getContentType'):
            return element.getContentType()
        return value

    security.declareProtected(CMFCorePermissions.View, 'get_portal_metadata')
    def get_portal_metadata(self, field):
        pmt = getToolByName(self, 'portal_metadata')
        policy = None
        try:
            spec = pmt.getElementSpec(field.accessor)
            policy = spec.getPolicy(self.portal_type)
        except:
            log_exc()
            return None, 0
        
        if not policy:
            policy = spec.getPolicy(None)
        
        return DisplayList(map(lambda x: (x,x), policy.allowedVocabulary())), \
               policy.enforceVocabulary()

    security.declareProtected(CMFCorePermissions.View, 'Vocabulary')
    def Vocabulary(self, key):
        vocab, enforce = None, 0
        field = self.getField(key)
        if field:
            if field.isMetadata:
                vocab, enforce = self.get_portal_metadata(field)

            if vocab is None:
                vocab, enforce = field.Vocabulary(self), field.enforceVocabulary

        if vocab is None:
            vocab = DisplayList()

        return vocab, enforce
    
    def __getitem__(self, key):
        """play nice with externaleditor again"""
        ## Also play nice with aq again... doh!
        if key not in self.Schema().keys() and key[:1] != "_": #XXX 2.2
            return getattr(self, key)
        accessor = getattr(self, self.Schema()[key].accessor)
        return accessor()

##     security.declareProtected(CMFCorePermissions.View, 'get')
##     def get(self, key, **kwargs):
##         """return editable version of content"""
##         accessor = self.Schema()[key]
##         return accessor()

##     def set(self, key, value, **kw):
##         mutator = getattr(self, self.Schema()[key].mutator)
##         mutator(value, **kw)
        
    def edit(self, **kwargs):
        self.update(**kwargs)

    def setDefaults(self):
        self.Schema().setDefaults(self)
            
    def update(self, **kwargs):
        self.Schema().updateAll(self, **kwargs)
        self._p_changed = 1
        self.reindexObject()
        
    def validate_field(self, name, value, errors):
        """
        write a method: validate_foo(new_value) -> "error" or None
        If there is a validate method defined for a given field invoke it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """
        methodName = "validate_%s" % name

        base = aq_base(self)
        if hasattr(base, methodName):
            method = getattr(base, methodName)
            result = method(value)
            if result is not None:
                errors[name] = result


    ##Pre/post validate hooks that will need to write errors
    ##into the errors dict directly using errors[fieldname] = ""
    security.declareProtected(CMFCorePermissions.View, 'pre_validate')            
    def pre_validate(self, REQUEST, errors):
        pass

    security.declareProtected(CMFCorePermissions.View, 'post_validate')            
    def post_validate(self, REQUEST, errors):
        pass
    
            
    security.declareProtected(CMFCorePermissions.View, 'validate')            
    def validate(self, REQUEST=None, errors=None, data=None, metadata=None):
        if errors is None:
            errors = {}
        self.pre_validate(REQUEST, errors)
        if errors:
            return errors
        
        self.Schema().validate(self, REQUEST=REQUEST, errors=errors, data=data, metadata=metadata)
        self.post_validate(REQUEST, errors)

        return errors
    
    security.declareProtected(CMFCorePermissions.View, 'SearchableText')
    def SearchableText(self):
        """full indexable text"""
        data = []
        for field in self.Schema().fields():
            if field.searchable != 1: continue
            try:
                method = getattr(self, field.accessor)
                datum = method()
                #if hasattr(dataum, 'isUnit'):
                #    data.append(datum.transform('text/plain').getData()
                #else:
                data.append(datum)
            except:
                pass

        data = [str(d) for d in data if d is not None]
        data = ' '.join(data)
        return data

    
    security.declareProtected(CMFCorePermissions.View, 'get_size' )
    def get_size( self ):
        """ Used for FTP and apparently the ZMI now too """
        size = 0
        for name in self.Schema().keys():
            field = getattr(self, name, None)
            if hasattr(field, "isUnit"):
                size += field.get_size()
            else:
                try:
                    size += len(field)
                except:
                    pass
                
        return size


    security.declareProtected(CMFCorePermissions.ModifyPortalContent, '_processForm')
    def _processForm(self, data=1, metadata=None):
        request = self.REQUEST
        form = request.form
        schema = self.Schema()
        fields = []

        if data: fields += schema.filterFields(metadata=0)
        if metadata: fields += schema.filterFields(metdata=1)

        form_keys = form.keys()
        for field in fields:
            if field.name in form_keys or "%s_file" % field.name in form_keys:
                text_format = None
                isFile = 0
                value = None
                
                # text field with formatting
                if hasattr(field, 'allowable_content_types') and field.allowable_content_types:
                    #was a mime_type specified
                    text_format = form.get("%s_text_format" % field.name) 
                # or a file?
                fileobj = form.get('%s_file' % field.name)
                if fileobj:
                    filename = getattr(fileobj, 'filename', '')
                    if filename != '':
                        value  =  fileobj
                        isFile = 1

                if not value:
                    value = form.get(field.name)
                
                #Set things by calling the mutator
                if not value: continue
                mutator = getattr(self, field.mutator)
                if text_format and not isFile:
                    mutator(value, mime_type=text_format)
                else:
                    mutator(value)
                    
        self.reindexObject()
        
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'processForm')
    def processForm(self, data=1, metadata=1):
        """Process the schema looking for data in the form"""
        self._processForm(data=data, metadata=metadata)
        

        
InitializeClass(BaseObject)

