import sys
from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base, aq_acquire, aq_inner, aq_parent
from Globals import InitializeClass
from OFS.ObjectManager import ObjectManager
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from ZPublisher.HTTPRequest import FileUpload
from ZODB.PersistentMapping import PersistentMapping
from debug import log, log_exc
from types import FileType
import operator

from Schema import Schema, Schemata
from Field import StringField, TextField
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
    _signature = None
    installMode = ['type', 'actions', 'navigation', 'validation', 'indexes']

    __implements__ = IBaseObject

    def __init__(self, oid, **kwargs):
        self.id = oid
        self._master_language = None
        self._translations_states = PersistentMapping()

    def initializeArchetype(self, **kwargs):
        """called by the generated addXXX factory in types tool"""
        try:
            self.initializeLayers()
            self.setDefaults()
            if kwargs:
                self.update(**kwargs)
            self._signature = self.Schema().signature()
        except:
            import traceback
            import sys
            sys.stdout.write('\n'.join(traceback.format_exception(*sys.exc_info())))

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
            parent = aq_parent(aq_inner(self))
            if parent is not None:
                parent.manage_renameObject(
                    self.id, value,
                    getattr(self, 'REQUEST', None)
                    )
            self._setId(value)

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
        mimetype = self.getContentType(key)
        if mimetype and hasattr(aq_base(mimetype), 'binary'):
            return mimetype.binary
        elif mimetype and mimetype.find('text') >= 0:
            return 0
        return 1

    security.declareProtected(CMFCorePermissions.View, 'isTransformable')
    def isTransformable(self, name):
        field = self.getField(name)
        return isinstance(field, TextField)  or not self.isBinary(name)

    security.declareProtected(CMFCorePermissions.View, 'widget')
    def widget(self, field_name, mode="view", **kwargs):
        widget = self.Schema()[field_name].widget
        return renderer.render(field_name, mode, widget, self,
                               **kwargs)

    security.declareProtected(CMFCorePermissions.View, 'getContentType')
    def getContentType(self, key):
        value = 'text/plain' #this should maybe be octet stream or something?
        field = self.getField(key)
        if field and hasattr(field, 'getContentType'):
            return field.getContentType(self)
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
        accessor = self.Schema()[key].getAccessor(self)
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
            if field.searchable != 1:
                continue
            method = getattr(self, field.accessor)
            try:
                datum =  method(mimetype="text/plain")
            except TypeError:
                # retry in case typeerror was raised because accessor doesn't
                # handle the mimetype argument
                try:
                    datum =  method()
                except:
                    datum =  ''
            if datum:
                data.append(datum)

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
            if data: fields += schema.filterFields(isMetadata=0)
            if metadata: fields += schema.filterFields(isMetadata=1)

        form_keys = form.keys()

        for field in fields:
            if field.getName() in form_keys or "%s_file" % field.getName() in form_keys:
                text_format = None
                isFile = 0
                value = None

                # text field with formatting
                if hasattr(field, 'allowable_content_types') and \
                   field.allowable_content_types:
                    #was a mimetype specified
                    text_format = form.get("%s_text_format" % field.getName())
                # or a file?
                fileobj = form.get('%s_file' % field.getName())
                if fileobj:
                    filename = getattr(fileobj, 'filename', '')
                    if filename != '':
                        value  =  fileobj
                        isFile = 1

                if not value:
                    value = form.get(field.getName())

                #Set things by calling the mutator
                if value is None: continue
                mutator = getattr(self, field.mutator)
                __traceback_info__ = (self, field, mutator)
                kwargs = {}

                if text_format and not isFile:
                    mutator(value, mimetype=text_format, **kwargs)
                else:
                    mutator(value, **kwargs)

        self.reindexObject()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'processForm')
    def processForm(self, data=1, metadata=0):
        """Process the schema looking for data in the form"""
        self._processForm(data=data, metadata=metadata)

    def Schemata(self):
        from Products.Archetypes.Schema import getSchemata
        return getSchemata(self)

    security.declarePrivate( '_datify' )
    def _datify( self, attrib ):
        """FIXME: overriden from DublinCore to deal with blank value..."""
        if attrib == 'None' or not attrib:
            attrib = ''
        elif not isinstance( attrib, DateTime ):
            attrib = DateTime( attrib )
        return attrib

    security.declarePublic( 'Date' )
    def Date( self ):
        """FIXME: overriden from DublinCore to deal with blank value...
        Dublin Core element - default date
        """
        # Return effective_date if set, modification date otherwise
        date = getattr(self, 'effective_date', None )
        if not date:
            date = self.modified()
        return date.ISO()


    # Handle schema updates ####################################################

#    def _compareDicts(self, d1, d2):
#        values = {}
#        for k,v in d1.items():
#            values[k] = (v,'N/A')
#        for k,v in d2.items():
#            if values.has_key(k):
#                values[k] = (values[k][0],v)
#            else:
#                values[k] = ('N/A', v)
#        keys = values.keys()
#        keys.sort()
#        import sys
#        for k in keys:
#            sys.stdout.write('%s: %s, %s\n' % (k, str(values[k][0]), str(values[k][1])))

    def _isSchemaCurrent(self):
        """Determine whether the current object's schema is up to date."""
        from Products.Archetypes.ArchetypeTool import getType
        return getType(self.meta_type)['signature'] == self._signature


    def _updateSchema(self, excluded_fields=[], out=None):
        """Update an object's schema when the class schema changes.
        For each field we use the existing accessor to get its value, then we
        re-initialize the class, then use the new schema mutator for each field
        to set the values again.  We also copy over any class methods to handle
        product refreshes gracefully (when a product refreshes, you end up with
        both the old version of the class and the new in memory at the same
        time -- you really should restart zope after doing a schema update)."""
        from Products.Archetypes.ArchetypeTool import getType

        print >> out, 'Updating %s' % (self.getId())

        old_schema = self.Schema()
        new_schema = getType(self.meta_type)['schema']

        obj_class = self.__class__
        current_class = getattr(sys.modules[self.__module__], self.__class__.__name__)
        if obj_class.schema != current_class.schema:
            # XXX This is kind of brutish.  We do this to make sure that old
            # class instances have the proper methods after a refresh.  The
            # best thing to do is to restart Zope after doing an update, and
            # the old versions of the class will disappear.
            # print >> out, 'Copying schema from %s to %s' % (current_class, obj_class)
            for k in current_class.__dict__.keys():
                obj_class.__dict__[k] = current_class.__dict__[k]
#            from Products.Archetypes.ArchetypeTool import generateClass
#            generateClass(obj_class)


        # read all the old values into a dict
        values = {}
        for f in new_schema.fields():
            name = f.getName()
            if name not in excluded_fields:
                try:
                    values[name] = self._migrateGetValue(name, new_schema)
                except ValueError:
                    if out != None:
                        print >> out, 'Unable to get %s.%s' % (str(self.getId()), name)

        # replace the schema
        # print >> out, 'Updating schema'
        from copy import deepcopy
        self.schema = deepcopy(new_schema)
        # print >> out, 'Reinitializing'
        self.initializeArchetype()

        # print >> out, 'Writing field values'
        for f in new_schema.fields():
            name = f.getName()
            if name not in excluded_fields and values.has_key(name):
                try:
                    self._migrateSetValue(name, values[name])
                except ValueError:
                    if out != None:
                        print >> out, 'Unable to set %s.%s to %s' % (str(self.getId()), name, str(values[name]))
        if out:
            return out


    def _migrateGetValue(self, name, new_schema=None):
        """Try to get a value from an object using a variety of methods."""
        schema = self.Schema()

        # First see if the new field name is managed by the current schema
        field = schema.get(name, None)
        if field:
            accessor = field.getAccessor(self)
            if accessor is not None:
                # yes -- return the value
                return accessor()

        # Nope -- see if the new accessor method is present in the current object.
        if new_schema:
            new_field = new_schema.get(name)
            accessor = new_field.getAccessor(self)
            if callable(accessor):
                try:
                    return accessor()
                except:
                    pass

        # Nope -- now see if the current object has an attribute with the same name
        # as the new field
        if hasattr(self, name):
            return getattr(self, name)

        raise ValueError, 'name = %s' % (name)


    def _migrateSetValue(self, name, value, old_schema=None):
        """Try to set an object value using a variety of methods."""
        schema = self.Schema()
        field = schema.get(name, None)
        # try using the field's mutator
        if field:
            mutator = field.getMutator(self)
            if mutator:
                mutator(value)
                return
        # try setting an existing attribute
        if hasattr(self, name):
            setattr(self, name, value)
            return
        raise ValueError, 'name = %s, value = %s' % (name, value)


    # I18N content management #################################################

    security.declarePublic("hasI18NContent")
    def hasI18NContent(self):
        """return true it the schema contains at least one I18N field

        not implemented in this release but we should keep the hasI18NContent
        methods !
        """
        return self.Schema().hasI18NContent()


    # subobject access ########################################################
    #
    # some temporary objects could be set by fields (for instance additional
    # images that may result from the transformation of a pdf field to html)
    #
    # those objects are specific to a session

    def addSubObjects(self, objects, REQUEST=None):
        """add a dictionnary of objects to session variable
        """
        if REQUEST is None:
            REQUEST = self.REQUEST
        key = self.absolute_url()
        session = REQUEST.SESSION
        defined = session.get(key, {})
        defined.update(objects)
        session[key] = defined

    def getSubObject(self, name, REQUEST, RESPONSE=None):
        """add a dictionnary of objects to session variable
        """
        try:
            data = REQUEST.SESSION[self.absolute_url()][name]
        except AttributeError:
            return
        except KeyError:
            return
        mtr = self.mimetypes_registry
        mt = mtr.classify(data, filename=name)
        return Wrapper(data, name, mt or 'application/octet')

    def __bobo_traverse__(self, REQUEST, name, RESPONSE=None):
        """ transparent access to session subobjects
        """
        # is it a registered sub object
        data = self.getSubObject(name, REQUEST, RESPONSE)
        if data is not None:
            return data
        # or a standard attribute (maybe acquired...)
        target = getattr(self, name, None)
        if target is not None:
            return target
        if RESPONSE is not None:
            RESPONSE.notFoundError("%s\n%s" % (name, ''))


class Wrapper:
    """wrapper object for access to sub objects """
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, data, filename, mimetype):
        self._data = data
        self._filename = filename
        self._mimetype = mimetype

    def __call__(self, REQUEST=None, RESPONSE=None):
        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE
        if RESPONSE is not None:
            mt = self._mimetype
            name =self._filename
            RESPONSE.setHeader('Content-type', str(mt))
            RESPONSE.setHeader('Content-Disposition',
                               'inline;filename=%s' % name)
            RESPONSE.setHeader('Content-Length', len(self._data))
        return self._data

InitializeClass(BaseObject)
