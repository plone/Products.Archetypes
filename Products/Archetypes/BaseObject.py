import sys
from App.class_init import InitializeClass

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.debug import log_exc
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import mapply
from Products.Archetypes.utils import fixSchema
from Products.Archetypes.utils import shasattr
from Products.Archetypes.Field import StringField
from Products.Archetypes.Field import TextField
from Products.Archetypes.Renderer import renderer
from Products.Archetypes.Schema import Schema
from Products.Archetypes.Schema import getSchemata
from Products.Archetypes.Widget import IdWidget
from Products.Archetypes.Widget import StringWidget
from Products.Archetypes.Marshall import RFC822Marshaller
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.interfaces import IReferenceable
from Products.Archetypes.interfaces import ISchema
from Products.Archetypes.interfaces.field import IFileField
from Products.Archetypes.validator import AttributeValidator
from Products.Archetypes.config import ATTRIBUTE_SECURITY
from Products.Archetypes.config import RENAME_AFTER_CREATION_ATTEMPTS

from Products.Archetypes.event import ObjectInitializedEvent
from Products.Archetypes.event import ObjectEditedEvent

from Products.Archetypes.interfaces import IMultiPageSchema
from Products.Archetypes.interfaces import IObjectPreValidation
from Products.Archetypes.interfaces import IObjectPostValidation

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from AccessControl.Permissions import copy_or_move as permission_copy_or_move
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import ImplicitAcquisitionWrapper
from Acquisition import ExplicitAcquisitionWrapper
from Acquisition import Explicit

from ComputedAttribute import ComputedAttribute
from ZODB.POSException import ConflictError
import transaction

from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName

from Referenceable import Referenceable

from ZPublisher import xmlrpc
from webdav.NullResource import NullResource

from zope import event
from zope.interface import implements, Interface
from zope.component import subscribers
from zope.component import queryMultiAdapter
from zope.component import queryUtility

# Import conditionally, so we don't introduce a hard depdendency
try:
    from plone.i18n.normalizer.interfaces import IUserPreferredURLNormalizer
    from plone.i18n.normalizer.interfaces import IURLNormalizer
    URL_NORMALIZER = True
except ImportError:
    URL_NORMALIZER = False

try:
    from plone.locking.interfaces import ILockable
    HAS_LOCKING = True
except ImportError:
    HAS_LOCKING = False

_marker = []

content_type = Schema((

    StringField(
        name='id',
        required=0, # Still actually required, but the widget will
                    # supply the missing value on non-submits
        mode='rw',
        permission=permission_copy_or_move,
        accessor='getId',
        mutator='setId',
        default=None,
        widget=IdWidget(
            label=_(u'label_short_name', default=u'Short Name'),
            description=_(u'help_shortname',
                          default=u'Should not contain spaces, underscores or mixed case. '
                                   'Short Name is part of the item\'s web address.'),
            visible={'view' : 'invisible'}
        ),
    ),

    StringField(
        name='title',
        required=1,
        searchable=1,
        default='',
        accessor='Title',
        widget=StringWidget(
            label_msgid='label_title',
            visible={'view' : 'invisible'},
            i18n_domain='plone',
        ),
    ),

    ), marshall = RFC822Marshaller())


class BaseObject(Referenceable):

    security = ClassSecurityInfo()

    # Protect AttributeStorage-based attributes. See the docstring of
    # AttributeValidator for the low-down.
    if ATTRIBUTE_SECURITY:
        attr_security = AttributeValidator()
        security.setDefaultAccess(attr_security)
        # Delete so it cannot be accessed anymore.
        del attr_security

    schema = content_type
    _signature = None

    installMode = ['type', 'actions', 'indexes']

    _at_rename_after_creation = False # rename object according to title?

    implements(IBaseObject, IReferenceable)

    def __init__(self, oid, **kwargs):
        self.id = oid

    security.declareProtected(permissions.ModifyPortalContent,
                              'initializeArchetype')
    def initializeArchetype(self, **kwargs):
        """Called by the generated add* factory in types tool.
        """
        try:
            self.initializeLayers()
            self.markCreationFlag()
            self.setDefaults()
            if kwargs:
                kwargs['_initializing_'] = True
                self.edit(**kwargs)
            self._signature = self.Schema().signature()
        except (ConflictError, KeyboardInterrupt):
            raise
        except:
            log_exc()

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        __traceback_info__ = (self, item, container)
        Referenceable.manage_afterAdd(self, item, container)
        self.initializeLayers(item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        __traceback_info__ = (self, item)
        Referenceable.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        __traceback_info__ = (self, item, container)
        self.cleanupLayers(item, container)
        Referenceable.manage_beforeDelete(self, item, container)

    security.declarePrivate('initializeLayers')
    def initializeLayers(self, item=None, container=None):
        self.Schema().initializeLayers(self, item, container)

    security.declarePrivate('cleanupLayers')
    def cleanupLayers(self, item=None, container=None):
        self.Schema().cleanupLayers(self, item, container)

    security.declareProtected(permissions.View, 'title_or_id')
    def title_or_id(self):
        """Returns the title if it is not blank and the id otherwise.
        """
        if shasattr(self, 'Title'):
            if callable(self.Title):
                return self.Title() or self.getId()

        return self.getId()

    security.declareProtected(permissions.View, 'getId')
    def getId(self):
        """Gets the object id.
        """
        return self.id

    security.declareProtected(permissions.ModifyPortalContent, 'setId')
    def setId(self, value):
        """Sets the object id.
        """
        if value != self.getId():
            parent = aq_parent(aq_inner(self))
            if parent is not None:
                # See Referenceable, keep refs on what is a move/rename
                self._v_cp_refs = 1
                # We can't rename if the object is locked
                if HAS_LOCKING:
                    lockable = ILockable(self)
                    was_locked = False
                    if lockable.locked():
                        was_locked = True
                        lockable.unlock()
                    parent.manage_renameObject(self.id, value)
                    if was_locked:
                        lockable.lock()
                else:
                    parent.manage_renameObject(self.id, value)
            self._setId(value)

    security.declareProtected(permissions.View, 'Type')
    def Type(self):
        """Dublin Core element - Object type.

        this method is redefined in ExtensibleMetadata but we need this
        at the object level (i.e. with or without metadata) to interact
        with the uid catalog.
        """
        if shasattr(self, 'getTypeInfo'):
            ti = self.getTypeInfo()
            if ti is not None:
                return ti.Title()
        return self.meta_type

    security.declareProtected(permissions.View, 'getField')
    def getField(self, key, wrapped=False):
        """Returns a field object.
        """
        return self.Schema().get(key)

    security.declareProtected(permissions.View, 'getWrappedField')
    def getWrappedField(self, key):
        """Gets a field by id which is explicitly wrapped.

        XXX Maybe we should subclass field from Acquisition.Explicit?
        """
        return ExplicitAcquisitionWrapper(self.getField(key), self)

    security.declareProtected(permissions.View, 'getDefault')
    def getDefault(self, field):
        """Return the default value of a field.
        """
        field = self.getField(field)
        return field.getDefault(self)

    security.declareProtected(permissions.View, 'isBinary')
    def isBinary(self, key):
        """Return wether a field contains binary data.
        """
        field = self.getField(key)
        if IFileField.providedBy(field):
            value = field.getBaseUnit(self)
            return value.isBinary()
        mimetype = self.getContentType(key)
        if mimetype and shasattr(mimetype, 'binary'):
            return mimetype.binary
        elif mimetype and mimetype.find('text') >= 0:
            return 0
        return 1

    security.declareProtected(permissions.View, 'isTransformable')
    def isTransformable(self, name):
        """Returns wether a field is transformable.
        """
        field = self.getField(name)
        return isinstance(field, TextField) or not self.isBinary(name)

    security.declareProtected(permissions.View, 'widget')
    def widget(self, field_name, mode="view", field=None, **kwargs):
        """Returns the rendered widget.
        """
        if field is None:
            field = self.Schema()[field_name]
        widget = field.widget
        return renderer.render(field_name, mode, widget, self, field=field,
                               **kwargs)

    security.declareProtected(permissions.View, 'getFilename')
    def getFilename(self, key=None):
        """Returns the filename from a field.
        """
        value = None

        if key is None:
            field = self.getPrimaryField()
        else:
            field = self.getField(key) or getattr(self, key, None)

        if field and shasattr(field, 'getFilename'):
            return field.getFilename(self)

        return value

    security.declareProtected(permissions.View, 'getContentType')
    def getContentType(self, key=None):
        """Returns the content type from a field.
        """
        value = 'text/plain'

        if key is None:
            field = self.getPrimaryField()
        else:
            field = self.getField(key) or getattr(self, key, None)

        if field and shasattr(field, 'getContentType'):
            return field.getContentType(self)

        return value

    # Backward compatibility
    # Note: ComputedAttribute should never be protected by a security
    # declaration! See http://dev.plone.org/archetypes/ticket/712
    content_type = ComputedAttribute(getContentType, 1)

    # XXX Where's get_content_type comes from??? There's no trace at both
    # Zope and CMF. It should be removed ASAP!
    security.declareProtected(permissions.View, 'get_content_type')
    get_content_type = getContentType

    security.declareProtected(permissions.ModifyPortalContent,
                              'setContentType')
    def setContentType(self, value, key=None):
        """Sets the content type of a field.
        """
        if key is None:
            field = self.getPrimaryField()
        else:
            field = self.getField(key) or getattr(self, key, None)

        if field and IFileField.providedBy(field):
            field.setContentType(self, value)

    security.declareProtected(permissions.ModifyPortalContent, 'setFilename')
    def setFilename(self, value, key=None):
        """Sets the filename of a field.
        """
        if key is None:
            field = self.getPrimaryField()
        else:
            field = self.getField(key) or getattr(self, key, None)

        if field and IFileField.providedBy(field):
            field.setFilename(self, value)

    security.declareProtected(permissions.View, 'getPrimaryField')
    def getPrimaryField(self):
        """The primary field is some object that responds to
        PUT/manage_FTPget events.
        """
        fields = self.Schema().filterFields(primary=1)
        if fields:
            return fields[0]
        return None

    security.declareProtected(permissions.View, 'get_portal_metadata')
    def get_portal_metadata(self, field):
        """Returns the portal_metadata for a field.
        """
        pmt = getToolByName(self, 'portal_metadata')
        policy = None
        try:
            schema = getattr(pmt, 'DCMI', None)
            spec = schema.getElementSpec(field.accessor)
            policy = spec.getPolicy(self.portal_type)
        except (ConflictError, KeyboardInterrupt):
            raise
        except:
            log_exc()
            return None, False

        if not policy:
            policy = spec.getPolicy(None)

        return DisplayList(map(lambda x: (x,x), policy.allowedVocabulary())), \
               policy.enforceVocabulary()

    security.declareProtected(permissions.View, 'Vocabulary')
    def Vocabulary(self, key):
        """Returns the vocabulary for a specified field.
        """
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
        """Overloads the object's item access.
        """
        # Don't allow key access to hidden attributes
        if key.startswith('_'):
            raise Unauthorized, key

        schema = self.Schema()
        keys = schema.keys()

        if key not in keys and not key.startswith('_'):
            # XXX Fix this in AT 1.4
            value= getattr(aq_inner(self).aq_explicit, key, _marker) or \
                   getattr(aq_parent(aq_inner(self)).aq_explicit, key, _marker)
            if value is _marker:
                raise KeyError, key
            else:
                return value

        field = schema[key]
        accessor = field.getEditAccessor(self)
        if not accessor:
            accessor = field.getAccessor(self)

        # This is the access mode used by external editor. We need the
        # handling provided by BaseUnit when its available
        kw = {'raw':1, 'field': field.__name__}
        value = mapply(accessor, **kw)
        return value

    security.declarePrivate('setDefaults')
    def setDefaults(self):
        """Sets the field values to the default values.
        """
        self.Schema().setDefaults(self)

    security.declareProtected(permissions.ModifyPortalContent, 'update')
    def update(self, **kwargs):
        """Changes the values of the field and reindex the object.
        """
        initializing = kwargs.get('_initializing_', False)
        if initializing:
            del kwargs['_initializing_']
        self.Schema().updateAll(self, **kwargs)
        self._p_changed = 1
        if not initializing:
            # Avoid double indexing during initialization.
            self.reindexObject()

    security.declareProtected(permissions.ModifyPortalContent, 'edit')
    edit = update

    security.declareProtected(permissions.View,
                              'validate_field')
    def validate_field(self, name, value, errors):
        """Field's validate hook.

        Write a method: validate_foo(new_value) -> "error" or None
        If there is a validate method defined for a given field invoke
        it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """
        methodName = "validate_%s" % name
        result = None
        if shasattr(self, methodName):
            method = getattr(self, methodName)
            result = method(value)
            if result is not None:
                errors[name] = result
        return result

    ## Pre/post validate hooks that will need to write errors
    ## into the errors dict directly using errors[fieldname] = ""
    security.declareProtected(permissions.View, 'pre_validate')
    def pre_validate(self, REQUEST=None, errors=None):
        pass

    security.declareProtected(permissions.View, 'post_validate')
    def post_validate(self, REQUEST=None, errors=None):
        pass

    security.declareProtected(permissions.View, 'validate')
    def validate(self, REQUEST=None, errors=None, data=None, metadata=None):
        """Validates the form data from the request.
        """
        if errors is None:
            errors = {}

        self.pre_validate(REQUEST, errors)

        for pre_validator in subscribers((self,), IObjectPreValidation):
            pre_errors = pre_validator(REQUEST)
            if pre_errors is not None:
                for field_name, error_message in pre_errors.items():
                    if field_name in errors:
                        errors[field_name] += " %s" % error_message
                    else:
                        errors[field_name] = error_message

        if errors:
            return errors
        self.Schema().validate(instance=self, REQUEST=REQUEST,
                               errors=errors, data=data, metadata=metadata)

        self.post_validate(REQUEST, errors)

        for post_validator in subscribers((self,), IObjectPostValidation):
            post_errors = post_validator(REQUEST)
            if post_errors is not None:
                for field_name, error_message in post_errors.items():
                    if field_name in errors:
                        errors[field_name] += " %s" % error_message
                    else:
                        errors[field_name] = error_message

        return errors

    security.declareProtected(permissions.View, 'SearchableText')
    def SearchableText(self):
        """All fields marked as 'searchable' are concatenated together
        here for indexing purpose.
        """
        data = []
        charset = self.getCharset()
        for field in self.Schema().fields():
            if not field.searchable:
                continue
            method = field.getIndexAccessor(self)
            try:
                datum =  method(mimetype="text/plain")
            except TypeError:
                # Retry in case typeerror was raised because accessor doesn't
                # handle the mimetype argument
                try:
                    datum =  method()
                except (ConflictError, KeyboardInterrupt):
                    raise
                except:
                    continue
            if datum:
                vocab = field.Vocabulary(self)
                if isinstance(datum, (list, tuple)):
                    # Unmangle vocabulary: we index key AND value
                    vocab_values = map(lambda value, vocab=vocab: vocab.getValue(value, ''), datum)
                    datum = list(datum)
                    datum.extend(vocab_values)
                    datum = ' '.join(datum)
                elif isinstance(datum, basestring):
                    if isinstance(datum, unicode):
                        datum = datum.encode(charset)
                    value = vocab.getValue(datum, '')
                    if isinstance(value, unicode):
                        value = value.encode(charset)
                    datum = "%s %s" % (datum, value, )

                if isinstance(datum, unicode):
                    datum = datum.encode(charset)
                data.append(str(datum))

        data = ' '.join(data)
        return data

    security.declareProtected(permissions.View, 'getCharset')
    def getCharset(self):
        """Returns the site default charset, or utf-8.
        """
        properties = getToolByName(self, 'portal_properties', None)
        if properties is not None:
            site_properties = getattr(properties, 'site_properties', None)
            if site_properties is not None:
                return site_properties.getProperty('default_charset')
            elif hasattr(properties, 'default_charset'):
                return properties.getProperty('default_charset') # CMF
        return 'utf-8'

    security.declareProtected(permissions.View, 'get_size')
    def get_size(self):
        """Used for FTP and apparently the ZMI now too.
        """
        size = 0
        for field in self.Schema().fields():
            size+=field.get_size(self)
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

        if not IMultiPageSchema.providedBy(self):
            fields = schema.fields()
        elif fieldset is not None:
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

            if not field.writeable(self):
                # If the field has no 'w' in mode, or the user doesn't
                # have the required permission, or the mutator doesn't
                # exist just bail out.
                continue

            try:
                # Pass validating=False to inform the widget that we
                # aren't in the validation phase, IOW, the returned
                # data will be forwarded to the storage
                result = field.widget.process_form(self, field, form,
                                                   empty_marker=_marker,
                                                   validating=False)
            except TypeError:
                # Support for old-style process_form methods
                result = field.widget.process_form(self, field, form,
                                                   empty_marker=_marker)

            if result is _marker or result is None:
                continue

            # Set things by calling the mutator
            mutator = field.getMutator(self)
            __traceback_info__ = (self, field, mutator)
            result[1]['field'] = field.__name__
            mapply(mutator, result[0], **result[1])

        self.reindexObject()

    security.declareProtected(permissions.ModifyPortalContent, 'processForm')
    def processForm(self, data=1, metadata=0, REQUEST=None, values=None):
        """Processes the schema looking for data in the form.
        """
        is_new_object = self.checkCreationFlag()
        self._processForm(data=data, metadata=metadata,
                          REQUEST=REQUEST, values=values)
        self.unmarkCreationFlag()
        if self._at_rename_after_creation and is_new_object:
            self._renameAfterCreation(check_auto_id=True)

        # Post create/edit hooks
        if is_new_object:
            event.notify(ObjectInitializedEvent(self))
            self.at_post_create_script()
        else:
            event.notify(ObjectEditedEvent(self))
            self.at_post_edit_script()

    # This method is only called once after object creation.
    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        pass

    # This method is called after every subsequent edit
    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self):
        pass

    security.declareProtected(permissions.ModifyPortalContent,
                              'markCreationFlag')
    def markCreationFlag(self):
        """Sets flag on the instance to indicate that the object hasn't been
        saved properly (unset in content_edit).

        This will only be done if a REQUEST is present to ensure that objects
        created programmatically are considered fully created.
        """
        req = getattr(self, 'REQUEST', None)
        if shasattr(req, 'get'):
            if req.get('SCHEMA_UPDATE', None) is not None:
                return
            meth = req.get('REQUEST_METHOD', None)
            # Ensure that we have an HTTP request, if you're creating an
            # object with something other than a GET or POST, then we assume
            # you are making a complete object.
            if meth in ('GET', 'POST', 'PUT', 'MKCOL'):
                self._at_creation_flag = True

    security.declareProtected(permissions.ModifyPortalContent,
                              'unmarkCreationFlag')
    def unmarkCreationFlag(self):
        """Removes the creation flag.
        """
        if shasattr(aq_inner(self), '_at_creation_flag'):
            self._at_creation_flag = False

    security.declareProtected(permissions.ModifyPortalContent,
                              'checkCreationFlag')
    def checkCreationFlag(self):
        """Returns True if the object has not been fully saved, False otherwise.
        """
        return getattr(aq_base(self), '_at_creation_flag', False)

    def generateNewId(self):
        """Suggest an id for this object.
        This id is used when automatically renaming an object after creation.
        """
        title = self.Title()
        # Can't work w/o a title
        if not title:
            return None

        # Don't do anything without the plone.i18n package
        if not URL_NORMALIZER:
            return None

        if not isinstance(title, unicode):
            charset = self.getCharset()
            title = unicode(title, charset)

        request = getattr(self, 'REQUEST', None)
        if request is not None:
            return IUserPreferredURLNormalizer(request).normalize(title)

        return queryUtility(IURLNormalizer).normalize(title)

    security.declarePrivate('_renameAfterCreation')
    def _renameAfterCreation(self, check_auto_id=False):
        """Renames an object like its normalized title.
        """
        old_id = self.getId()
        if check_auto_id and not self._isIDAutoGenerated(old_id):
            # No auto generated id
            return False

        new_id = self.generateNewId()
        if new_id is None:
            return False

        invalid_id = True
        check_id = getattr(self, 'check_id', None)
        if check_id is not None:
            invalid_id = check_id(new_id, required=1)

        # If check_id told us no, or if it was not found, make sure we have an
        # id unique in the parent folder.
        if invalid_id:
            unique_id = self._findUniqueId(new_id)
            if unique_id is not None:
                if check_id is None or check_id(new_id, required=1):
                    new_id = unique_id
                    invalid_id = False

        if not invalid_id:
            # Can't rename without a subtransaction commit when using
            # portal_factory!
            transaction.savepoint(optimistic=True)
            self.setId(new_id)
            return new_id

        return False

    security.declarePrivate('_findUniqueId')
    def _findUniqueId(self, id):
        """Find a unique id in the parent folder, based on the given id, by
        appending -n, where n is a number between 1 and the constant
        RENAME_AFTER_CREATION_ATTEMPTS, set in config.py. If no id can be
        found, return None.
        """
        check_id = getattr(self, 'check_id', None)
        if check_id is None:
            parent = aq_parent(aq_inner(self))
            parent_ids = parent.objectIds()
            check_id = lambda id, required: id in parent_ids

        invalid_id = check_id(id, required=1)
        if not invalid_id:
            return id

        idx = 1
        while idx <= RENAME_AFTER_CREATION_ATTEMPTS:
            new_id = "%s-%d" % (id, idx)
            if not check_id(new_id, required=1):
                return new_id
            idx += 1

        return None

    security.declarePrivate('_isIDAutoGenerated')
    def _isIDAutoGenerated(self, id):
        """Avoid busting setDefaults if we don't have a proper acquisition
        context.
        """
        plone_tool = getToolByName(self, 'plone_utils', None)
        if plone_tool is not None and \
           shasattr(plone_tool, 'isIDAutoGenerated'):
            return plone_tool.isIDAutoGenerated(id)
        return False

    security.declareProtected(permissions.View, 'Schemata')
    def Schemata(self):
        """Returns the Schemata for the Object.
        """
        return getSchemata(self)

    def Schema(self):
        """Return a (wrapped) schema instance for this object instance.
        """
        return ImplicitAcquisitionWrapper(ISchema(self), self)

    security.declarePrivate('_isSchemaCurrent')
    def _isSchemaCurrent(self):
        """Determines whether the current object's schema is up to date.
        """
        return self._signature == self.Schema().signature()

    security.declarePrivate('_updateSchema')
    def _updateSchema(self, excluded_fields=[], out=None,
                      remove_instance_schemas=False):
        """Updates an object's schema when the class schema changes.

        For each field we use the existing accessor to get its value,
        then we re-initialize the class, then use the new schema
        mutator for each field to set the values again.

        We also copy over any class methods to handle product
        refreshes gracefully (when a product refreshes, you end up
        with both the old version of the class and the new in memory
        at the same time -- you really should restart zope after doing
        a schema update).
        """
        if out is not None:
            print >> out, 'Updating %s' % (self.getId())

        if remove_instance_schemas and 'schema' in self.__dict__:
            if out is not None:
                print >> out, 'Removing schema from instance dict.'
            del self.schema
        new_schema = self.Schema()

        # Read all the old values into a dict
        values = {}
        mimes = {}
        for f in new_schema.fields():
            name = f.getName()
            if name in excluded_fields:
                continue
            if f.type == "reference":
                continue
            try:
                values[name] = self._migrateGetValue(name, new_schema)
            except ValueError:
                if out is not None:
                    print >> out, ('Unable to get %s.%s'
                                   % (str(self.getId()), name))
            else:
                if shasattr(f, 'getContentType'):
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

        # Set a request variable to avoid resetting the newly created flag
        req = getattr(self, 'REQUEST', None)
        if req is not None:
            req.set('SCHEMA_UPDATE','1')
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
                    if out is not None:
                        print >> out, ('Unable to set %s.%s to '
                                       '%s' % (str(self.getId()),
                                               name, str(values[name])))
        # Make sure the changes are persisted
        self._p_changed = 1
        if out is not None:
            return out

    security.declarePrivate('_migrateGetValue')
    def _migrateGetValue(self, name, new_schema=None):
        """Try to get a value from an object using a variety of methods."""
        schema = self.Schema()
        # Migrate pre-AT 1.3 schemas.
        schema = fixSchema(schema)
        # First see if the new field name is managed by the current schema
        field = schema.get(getattr(new_schema.get(name,None),'old_field_name',name), None)
        if field:
            # At very first try to use the BaseUnit itself
            try:
                if IFileField.providedBy(field):
                    return field.getBaseUnit(self)
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

            # First try the edit accessor
            try:
                editAccessor = field.getEditAccessor(self)
                if editAccessor:
                    return editAccessor()
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

            # No luck -- now try the accessor
            try:
                accessor = field.getAccessor(self)
                if accessor:
                    return accessor()
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass
            # No luck use standard method to get the value
            return field.get(self)

            # Still no luck -- try to get the value directly
            # this part should be remove because for some fields this will fail
            # if you get the value directly for example for FixPointField
            # stored value is (0,0) but the input value is a string.
            # at this time FixPointField fails if he got a tuple as input value
            # Because of this line value = value.replace(',','.')
            try:
                return self[field.getName()]
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

        # Nope -- see if the new accessor method is present
        # in the current object.
        if new_schema:
            new_field = new_schema.get(name)
            # Try the new edit accessor
            try:
                editAccessor = new_field.getEditAccessor(self)
                if editAccessor:
                    return editAccessor()
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

            # Nope -- now try the accessor
            try:
                accessor = new_field.getAccessor(self)
                if accessor:
                    return accessor()
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

            # Still no luck -- try to get the value directly using the new name
            try:
                return self[new_field.getName()]
            except (ConflictError, KeyboardInterrupt):
                raise
            except:
                pass

        # Nope -- now see if the current object has an attribute
        # with the same name
        # as the new field
        if shasattr(self, name):
            return getattr(self, name)

        raise ValueError, 'name = %s' % (name)

    security.declarePrivate('_migrateSetValue')
    def _migrateSetValue(self, name, value, old_schema=None, **kw):
        """Try to set an object value using a variety of methods."""
        schema = self.Schema()
        # Migrate pre-AT 1.3 schemas.
        schema = fixSchema(schema)
        field = schema.get(name, None)
        # Try using the field's mutator
        if field:
            mutator = field.getMutator(self)
            if mutator is not None:
                try:
                    args = [value,]
                    mapply(mutator, *args, **kw)
                    return
                except (ConflictError, KeyboardInterrupt):
                    raise
                except:
                    log_exc()
        else:
            # Try setting an existing attribute
            if shasattr(self, name):
                setattr(self, name, value)
                return
        raise ValueError, 'name = %s, value = %s' % (name, value)

    security.declareProtected(permissions.View, 'isTemporary')
    def isTemporary(self):
        """Checks to see if we are created as temporary object by
        portal factory.
        """
        parent = aq_parent(aq_inner(self))
        return shasattr(parent, 'meta_type') and \
               parent.meta_type == 'TempFolder'

    security.declareProtected(permissions.View, 'getFolderWhenPortalFactory')
    def getFolderWhenPortalFactory(self):
        """Returns the folder where this object was created temporarily.
        """
        ctx = aq_inner(self)
        if not ctx.isTemporary():
            # Not a temporary object!
            return aq_parent(ctx)
        utool = getToolByName(self, 'portal_url')
        portal_object = utool.getPortalObject()

        while ctx.getId() != 'portal_factory':
            # Find the portal factory object
            if ctx == portal_object:
                # uups, shouldn't happen!
                return ctx
            ctx = aq_parent(ctx)
        # ctx is now the portal_factory in our parent folder
        return aq_parent(ctx)

    #
    # Subobject Access
    #
    # Some temporary objects could be set by fields (for instance
    # additional images that may result from the transformation of
    # a PDF field to html).
    #
    # Those objects are specific to a session.
    #

    security.declareProtected(permissions.ModifyPortalContent,
                              'addSubObjects')
    def addSubObjects(self, objects, REQUEST=None):
        """Adds a dictionary of objects to a volatile attribute.
        """
        if objects:
            storage = getattr(aq_base(self), '_v_at_subobjects', None)
            if storage is None:
                setattr(self, '_v_at_subobjects', {})
                storage = getattr(aq_base(self), '_v_at_subobjects')
            for name, obj in objects.items():
                storage[name] = aq_base(obj)

    security.declareProtected(permissions.View, 'getSubObject')
    def getSubObject(self, name, REQUEST, RESPONSE=None):
        """Gets a dictionary of objects from a volatile attribute.
        """
        storage = getattr(aq_base(self), '_v_at_subobjects', None)
        if storage is None:
            return None

        data = storage.get(name, None)
        if data is None:
            return None

        mtr = self.mimetypes_registry
        mt = mtr.classify(data, filename=name)
        return Wrapper(data, name, str(mt) or 'application/octet-stream').__of__(self)

    def __bobo_traverse__(self, REQUEST, name):
        """Allows transparent access to session subobjects.
        """
        # sometimes, the request doesn't have a response, e.g. when
        # PageTemplates traverse through the object path, they pass in
        # a phony request (a dict).
        RESPONSE = getattr(REQUEST, 'RESPONSE', None)

        # Is it a registered sub object
        data = self.getSubObject(name, REQUEST, RESPONSE)
        if data is not None:
            return data
        # Or a standard attribute (maybe acquired...)
        target = None
        method = REQUEST.get('REQUEST_METHOD', 'GET').upper()
        # Logic from "ZPublisher.BaseRequest.BaseRequest.traverse"
        # to check whether this is a browser request
        if (len(REQUEST.get('TraversalRequestNameStack', ())) == 0 and
            not (method in ('GET', 'HEAD', 'POST') and not
                 isinstance(RESPONSE, xmlrpc.Response))):
            if shasattr(self, name):
                target = getattr(self, name)
        else:
            if shasattr(self, name): # attributes of self come first
                target = getattr(self, name)
            else: # then views
                target = queryMultiAdapter((self, REQUEST), Interface, name)
                if target is not None:
                    # We don't return the view, we raise an
                    # AttributeError instead (below)
                    target = None
                else: # then acquired attributes
                    target = getattr(self, name, None)

        if target is not None:
            return target
        elif (method not in ('GET', 'POST') and not
              isinstance(RESPONSE, xmlrpc.Response) and
              REQUEST.maybe_webdav_client):
            return NullResource(self, name, REQUEST).__of__(self)
        else:
            # Raising AttributeError will look up views for us
            raise AttributeError(name)

InitializeClass(BaseObject)

class Wrapper(Explicit):
    """Wrapper object for access to sub objects."""
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
            name = self._filename
            RESPONSE.setHeader('Content-type', str(mt))
            RESPONSE.setHeader('Content-Disposition',
                               'inline;filename=%s' % name)
            RESPONSE.setHeader('Content-Length', len(self._data))
        return self._data

MinimalSchema = BaseObject.schema

__all__ = ('BaseObject', 'MinimalSchema')
