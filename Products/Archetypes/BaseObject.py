from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.interfaces.base import IBaseObject, IBaseUnit
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.utils import DisplayList, mapply
from Products.Archetypes.Field import StringField, TextField
from Products.Archetypes.Renderer import renderer
from Products.Archetypes.Schema import Schema, Schemata
from Products.Archetypes.Widget import IdWidget, StringWidget
from Products.Archetypes.Marshall import RFC822Marshaller

from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base, aq_acquire, aq_inner, aq_parent
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import ConflictError

from ZPublisher import xmlrpc

_marker = []

content_type = Schema((
    StringField('id',
                required=0, ## Still actually required, but
                            ## the widget will supply the missing value
                            ## on non-submits
                mode="rw",
                accessor="getId",
                mutator="setId",
                default=None,
                widget=IdWidget(
    label="Short Name",
    label_msgid="label_short_name",
    description="Should not contain spaces, underscores or mixed case. "\
    "Short Name is part of the item's web address.",
    description_msgid="help_shortname",
    visible={'view' : 'invisible'},
    i18n_domain="plone"),
                ),

    StringField('title',
                required=1,
                searchable=1,
                default='',
                accessor='Title',
                widget=StringWidget(
    label_msgid="label_title",
    description=None,
    i18n_domain="plone"),
                )),

    marshall = RFC822Marshaller()
                      )

class BaseObject(Implicit):

    security = ClassSecurityInfo()

    schema = type = content_type
    _signature = None

    installMode = ['type', 'actions', 'indexes']

    __implements__ = IBaseObject

    def __init__(self, oid, **kwargs):
        self.id = oid

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'initializeArchetype')
    def initializeArchetype(self, **kwargs):
        """called by the generated addXXX factory in types tool"""
        try:
            self.initializeLayers()
            self.setDefaults()
            if kwargs:
                self.update(**kwargs)
            self._signature = self.Schema().signature()
        except:
            log_exc()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        self.initializeLayers(item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        pass

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        self.cleanupLayers(item, container)

    security.declarePrivate('initializeLayers')
    def initializeLayers(self, item=None, container=None):
        self.Schema().initializeLayers(self, item, container)

    security.declarePrivate('cleanupLayers')
    def cleanupLayers(self, item=None, container=None):
        self.Schema().cleanupLayers(self, item, container)

    security.declareProtected(CMFCorePermissions.View,
                              'title_or_id')
    def title_or_id(self):
        """
        Utility that returns the title if it is not blank and the id
        otherwise.
        """
        if hasattr(aq_base(self), 'Title'):
            if callable(self.Title):
                return self.Title() or self.getId()

        return self.getId()

    security.declareProtected(CMFCorePermissions.View,
                              'getId')
    def getId(self):
        """get the objects id"""
        return self.id

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setId')
    def setId(self, value):
        if value != self.getId():
            parent = aq_parent(aq_inner(self))
            if parent is not None:
                parent.manage_renameObject(
                    self.id, value,
                    )
            self._setId(value)

    security.declareProtected(CMFCorePermissions.View,
                              'Type')
    def Type( self ):
        """Dublin Core element - Object type

        this method is redefined in ExtensibleMetadata but we need this
        at the object level (i.e. with or without metadata) to interact
        with the uid catalog
        """
        if hasattr(aq_base(self), 'getTypeInfo'):
            ti = self.getTypeInfo()
            if ti is not None:
                return ti.Title()
        return self.meta_type

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

    security.declareProtected(CMFCorePermissions.View, 'getPrimaryField')
    def getPrimaryField(self):
        """The primary field is some object that responds to
        PUT/manage_FTPget events.
        """
        fields = self.Schema().filterFields(primary=1)
        if fields: return fields[0]
        return None

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
        schema = self.Schema()
        keys = schema.keys()
        if key not in keys and key[:1] != "_": #XXX 2.2
            return getattr(self, key, None) or \
                   getattr(aq_parent(aq_inner(self)), key, None)

        accessor = schema[key].getEditAccessor(self)
        if not accessor:
            accessor = schema[key].getAccessor(self)

        # This is the access mode used by external editor. We need the
        # handling provided by BaseUnit when its available
        kw = {'raw':1}
        value = mapply(accessor, **kw)

        return value

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'edit')
    def edit(self, **kwargs):
        self.update(**kwargs)

    security.declarePrivate('setDefaults')
    def setDefaults(self):
        self.Schema().setDefaults(self)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'update')
    def update(self, **kwargs):
        self.Schema().updateAll(self, **kwargs)
        self._p_changed = 1
        self.reindexObject()

    security.declareProtected(CMFCorePermissions.View,
                              'validate_field')
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


    ## Pre/post validate hooks that will need to write errors
    ## into the errors dict directly using errors[fieldname] = ""
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
        """All fields marked as 'searchable' are concatenated together
        here for indexing purpose"""
        data = []
        charset = self.getCharset()
        for field in self.Schema().fields():
            if not field.searchable:
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
                    continue
            if datum:
                type_datum = type(datum)
                if type_datum is type([]) or type_datum is type(()):
                    datum = ' '.join(datum)
                # FIXME: we really need an unicode policy !
                if type_datum is type(u''):
                    datum = datum.encode(charset)
                data.append(str(datum))

        data = ' '.join(data)
        return data

    security.declareProtected(CMFCorePermissions.View, 'getCharset')
    def getCharset(self):
        """ Return site default charset, or utf-8 """
        purl = getToolByName(self, 'portal_url')
        container = purl.getPortalObject()
        if getattr(container, 'getCharset', None):
            return container.getCharset()

        encoding = 'utf-8'
        p_props = getToolByName(self, 'portal_properties', None)
        if p_props is not None:
            site_props = getattr(p_props, 'site_properties', None)
            if site_props is not None:
                encoding = site_props.getProperty('default_charset')

        return encoding


    security.declareProtected(CMFCorePermissions.View, 'get_size' )
    def get_size( self ):
        """ Used for FTP and apparently the ZMI now too """
        size = 0
        for name in self.Schema().keys():
            value = self[name]
            if IBaseUnit.isImplementedBy(value):
                size += value.get_size()
            else:
                if value is not None:
                    try:
                        size += len(value)
                    except (TypeError, AttributeError):
                        size += len(str(value))

        return size

    security.declarePrivate('_processForm')
    def _processForm(self, data=1, metadata=None, REQUEST=None, values=None):
        request = REQUEST or self.REQUEST
        if values:
            form = values
        else:
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
            ## Delegate to the widget for processing of the form
            ## element.  This means that if the widget needs _n_
            ## fields under a naming convention it can handle this
            ## internally.  The calling API is process_form(instance,
            ## field, form) where instance should rarely be needed,
            ## field is the field object and form is the dict. of
            ## kv_pairs from the REQUEST
            ##
            ## The product of the widgets processing should be:
            ##   (value, **kwargs) which will be passed to the mutator
            ##   or None which will simply pass
            widget = field.widget
            result = widget.process_form(self, field, form,
                                         empty_marker=_marker)
            if result is _marker or result is None: continue

            # Set things by calling the mutator
            mutator = field.getMutator(self)
            __traceback_info__ = (self, field, mutator)
            mutator(result[0], **result[1])

        self.reindexObject()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'processForm')
    def processForm(self, data=1, metadata=0, REQUEST=None, values=None):
        """Process the schema looking for data in the form"""
        self._processForm(data=data, metadata=metadata,
                          REQUEST=REQUEST, values=values)

    security.declareProtected(CMFCorePermissions.View,
                              'Schemata')
    def Schemata(self):
        from Products.Archetypes.Schema import getSchemata
        return getSchemata(self)

    security.declarePrivate('_isSchemaCurrent')
    def _isSchemaCurrent(self):
        """Determine whether the current object's schema is up to date."""
        from Products.Archetypes.ArchetypeTool import getType, _guessPackage
        package = _guessPackage(self.__module__)
        return getType(self.meta_type, package)['signature'] == self._signature


    security.declarePrivate('_updateSchema')
    def _updateSchema(self, excluded_fields=[], out=None):
        """Update an object's schema when the class schema changes.

        For each field we use the existing accessor to get its value,
        then we re-initialize the class, then use the new schema
        mutator for each field to set the values again.

        We also copy over any class methods to handle product
        refreshes gracefully (when a product refreshes, you end up
        with both the old version of the class and the new in memory
        at the same time -- you really should restart zope after doing
        a schema update).
        """
        from Products.Archetypes.ArchetypeTool import getType, _guessPackage
        import sys

        if out:
            print >> out, 'Updating %s' % (self.getId())

        old_schema = self.Schema()
        package = _guessPackage(self.__module__)
        new_schema = getType(self.meta_type, package)['schema']

        # read all the old values into a dict
        values = {}
        mimes = {}
        for f in new_schema.fields():
            name = f.getName()
            if name not in excluded_fields:
                try:
                    values[name] = self._migrateGetValue(name, new_schema)
                except ValueError:
                    if out != None:
                        print >> out, ('Unable to get %s.%s'
                                       % (str(self.getId()), name))
                else:
                    if hasattr(f, 'getContentType'):
                        mimes[name] = f.getContentType(self)

        obj_class = self.__class__
        current_class = getattr(sys.modules[self.__module__],
                                self.__class__.__name__)
        if obj_class.schema != current_class.schema:
            # XXX This is kind of brutish.  We do this to make sure that old
            # class instances have the proper methods after a refresh.  The
            # best thing to do is to restart Zope after doing an update, and
            # the old versions of the class will disappear.

            for k in current_class.__dict__.keys():
                obj_class.__dict__[k] = current_class.__dict__[k]


        # replace the schema
        from copy import deepcopy
        self.schema = deepcopy(new_schema)
        self.initializeArchetype()

        for f in new_schema.fields():
            name = f.getName()
            kw = {}
            if name not in excluded_fields and values.has_key(name):
                if mimes.has_key(name):
                    kw['mimetype'] = mimes[name]
                try:
                    self._migrateSetValue(name, values[name], **kw)
                except ValueError:
                    if out != None:
                        print >> out, ('Unable to set %s.%s to '
                                       '%s' % (str(self.getId()),
                                               name, str(values[name])))

        self._p_changed = 1 # make sure the changes are persisted

        if out:
            return out


    security.declarePrivate('_migrateGetValue')
    def _migrateGetValue(self, name, new_schema=None):
        """Try to get a value from an object using a variety of methods."""
        schema = self.Schema()

        # First see if the new field name is managed by the current schema
        field = schema.get(name, None)
        if field:
            # first try the edit accessor
            try:
                editAccessor = field.getEditAccessor(self)
                if editAccessor:
                    return editAccessor()
            except ConflictError:
                raise
            except:
                pass
            # no luck -- now try the accessor
            try:
                accessor = field.getAccessor(self)
                if accessor:
                    return accessor()
            except ConflictError:
                raise
            except:
                pass
            # still no luck -- try to get the value directly
            try:
                return self[field.getName()]
            except ConflictError:
                raise
            except:
                pass

        # Nope -- see if the new accessor method is present
        # in the current object.
        if new_schema:
            new_field = new_schema.get(name)
            # try the new edit accessor
            try:
                editAccessor = new_field.getEditAccessor(self)
                if editAccessor:
                    return editAccessor()
            except ConflictError:
                raise
            except:
                pass

            # nope -- now try the accessor
            try:
                accessor = new_field.getAccessor(self)
                if accessor:
                    return accessor()
            except ConflictError:
                raise
            except:
                pass
            # still no luck -- try to get the value directly using the new name
            try:
                return self[new_field.getName()]
            except ConflictError:
                raise
            except:
                pass

        # Nope -- now see if the current object has an attribute
        # with the same name
        # as the new field
        if hasattr(self, name):
            return getattr(self, name)

        raise ValueError, 'name = %s' % (name)


    security.declarePrivate('_migrateSetValue')
    def _migrateSetValue(self, name, value, old_schema=None, **kw):
        """Try to set an object value using a variety of methods."""
        schema = self.Schema()
        field = schema.get(name, None)
        # try using the field's mutator
        if field:
            mutator = field.getMutator(self)
            if mutator is not None:
                try:
                    args = [value,]
                    mapply(mutator, *args, **kw)
                    return
                except ConflictError:
                    raise
                except:
                    log_exc()
        # try setting an existing attribute
        if hasattr(self, name):
            setattr(self, name, value)
            return
        raise ValueError, 'name = %s, value = %s' % (name, value)


    # subobject access ########################################################
    #
    # some temporary objects could be set by fields (for instance additional
    # images that may result from the transformation of a pdf field to html)
    #
    # those objects are specific to a session

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'addSubObjects')
    def addSubObjects(self, objects, REQUEST=None):
        """add a dictionnary of objects to session variable
        """
        if objects:
            if REQUEST is None:
                REQUEST = self.REQUEST
            key = '/'.join(self.getPhysicalPath())
            session = REQUEST.SESSION
            defined = session.get(key, {})
            defined.update(objects)
            session[key] = defined

    security.declareProtected(CMFCorePermissions.View,
                              'getSubObject')
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
        method = REQUEST.get('REQUEST_METHOD', 'GET').upper()
        if (not method in ('GET', 'POST', 'HEAD') and
            not isinstance(RESPONSE, xmlrpc.Response)):
            from webdav.NullResource import NullResource
            return NullResource(self, name, REQUEST).__of__(self)
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
