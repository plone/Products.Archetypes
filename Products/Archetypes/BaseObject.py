from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base, aq_acquire, aq_inner, aq_parent
from Globals import InitializeClass
from OFS.ObjectManager import ObjectManager
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from ZPublisher.HTTPRequest import FileUpload
from debug import log, log_exc
from types import FileType
import operator

from Schema import Schema, Schemata
from Field import StringField
from Widget import IdWidget, StringWidget
from utils import DisplayList
from interfaces.base import IBaseObject
from interfaces.referenceable import IReferenceable

from Renderer import renderer

content_type = Schema((
    StringField('id',
                required=1,
                mode="rw",
                accessor="getId",
                mutator="setId",
                default=None,
                widget=IdWidget(label_msgid="label_name",
                                description_msgid="help_name",
                                i18n_domain="plone"),
                ),

    StringField('title',
                required=1,
                searchable=1,
                default='',
                accessor='Title',
                widget=StringWidget(label_msgid="label_title",
                                    description_msgid="help_title",
                                    i18n_domain="plone"),
                ),
    ))

class BaseObject(Implicit):
    security = ClassSecurityInfo()

    schema = type = content_type
    installMode = ['type', 'actions', 'navigation', 'validation', 'indexes']

    __implements__ = IBaseObject

    def __init__(self, oid, **kwargs):
        self.id = oid

    def initializeArchetype(self, **kwargs):
        """called by the generated addXXX factory in types tool"""
        self.initializeLayers()
        self.setDefaults()
        if kwargs:
            self.update(**kwargs)

    def manage_afterAdd(self, item, container):
        self.initializeLayers(item, container)

    def manage_afterClone(self, item):
        pass

    def manage_beforeDelete(self, item, container):
        self.cleanupLayers(item, container)

    def initializeLayers(self, item=None, container=None):
        self.Schema().initializeLayers(self, item, container)

    def cleanupLayers(self, item=None, container=None):
        self.Schema().cleanupLayers(self, item, container)

    security.declarePublic("title_or_id")
    def title_or_id(self):
        """
        Utility that returns the title if it is not blank and the id
        otherwise.
        """
        if hasattr(aq_base(self), 'Title'):
            if callable(self.Title):
                return self.Title() or self.getId()

        return self.getId()

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

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'getField')
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
        widget = self.Schema()[field_name].widget
        return renderer.render(field_name, mode, widget, self,
                               **kwargs)

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
                vocab, enforce = field.Vocabulary(self), \
                                 field.enforceVocabulary

        if vocab is None:
            vocab = DisplayList()

        return vocab, enforce

    def __getitem__(self, key):
        """play nice with externaleditor again"""
        if key not in self.Schema().keys() and key[:1] != "_": #XXX 2.2
            return getattr(self, key, None) or getattr(aq_parent(aq_inner(self)), key, None)
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
        If there is a validate method defined for a given field invoke
        it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """

        methodName = "validate_%s" % name

        if hasattr(aq_base(self), methodName):
            method = getattr(self, methodName)
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
        if REQUEST is None:
            REQUEST = self.REQUEST
        if errors is None:
            errors = {}
        self.pre_validate(REQUEST, errors)
        if errors:
            return errors

        self.Schema().validate(self, REQUEST=REQUEST, errors=errors, 
                               data=data, metadata=metadata)
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


    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              '_processForm')
    def _processForm(self, data=1, metadata=None):
        request = self.REQUEST
        form = request.form
        fieldset = form.get('fieldset', None)
        schema = self.Schema()
        schemata = self.Schemata()
        fields = []

        if fieldset is not None:
            fields = schemata[fieldset].fields()
        else:
            if data: fields += schema.filterFields(metadata=0)
            if metadata: fields += schema.filterFields(metadata=1)

        form_keys = form.keys()
        for field in fields:
            if field.name in form_keys or "%s_file" % field.name in form_keys:
                text_format = None
                isFile = 0
                value = None

                # text field with formatting
                if hasattr(field, 'allowable_content_types') and \
                   field.allowable_content_types:
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
                __traceback_info__ = (self, field, mutator)
                if text_format and not isFile:
                    mutator(value, mime_type=text_format)
                else:
                    mutator(value)

        self.reindexObject()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'processForm')
    def processForm(self, data=1, metadata=0):
        """Process the schema looking for data in the form"""
        self._processForm(data=data, metadata=metadata)

    def Schemata(self):
        from Products.Archetypes.Schema import getSchemata
        return getSchemata(self)

InitializeClass(BaseObject)

