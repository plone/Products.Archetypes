"""
PloneCollectorNG - A Plone-based bugtracking system

(C) by Andreas Jung, andreas@andreas-jung.com & others

License: see LICENSE.txt

$Id: Schema.py,v 1.53.2.1 2004/01/31 17:16:39 ajung Exp $
"""

from types import FileType, ListType, TupleType

from Globals import Persistent, InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from Products.CMFCore.CMFCorePermissions import *
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import mapply, OrderedDict
from Products.Archetypes.Layer import DefaultLayerContainer
from Products.Archetypes.interfaces.layer import ILayerContainer, ILayerRuntime, ILayer 
from Products.Archetypes.interfaces.field import IField, IObjectField, IImageField
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.Storage import AttributeStorage, MetadataStorage

try:
    from generator.i18n import translate
except ImportError:
    from Products.generator.i18n import translate

def getNames(schema):
    """Returns a list of all fieldnames in the given schema."""
    return [f.getName() for f in schema.fields()]


def getSchemata(obj):
    """Returns an ordered dictionary, which maps all Schemata names to fields
    that belong to the Schemata."""

    schema = obj.Schema()
    schemata = OrderedDict()
    for f in schema.fields():
        sub = schemata.get(f.schemata, Schemata(name=f.schemata))
        sub.addField(f)
        schemata[f.schemata] = ImplicitAcquisitionWrapper(sub, obj)

    return schemata
# Some replacement classes for Archetypes

class Schemata(Persistent):

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, name='default', fields=()):
        self.clear()
        self.__name__ = name
        for f in fields: self.addField(f)

    security.declareProtected(ModifyPortalContent, 'clear')
    def clear(self):
        self._names = []
        self._fields = {}

    security.declareProtected(View, 'getName')
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

    security.declareProtected(ModifyPortalContent, 'addField')
    def addField(self, field):
        """ add a field """
#        if field.getName() in self._names:
#            raise KeyError("Field '%s' already exists" % field.getName())
        self._names.append(field.getName())
        self._fields[field.getName()] = field
        self._p_changed = 1

    security.declareProtected(ModifyPortalContent, 'delField')
    def delField(self, field_id):
        """ remove a field """

        if not field_id in self._names:
            raise KeyError("Field '%s' does not exists" % field_id)
        self._names.remove(field_id)
        del self._fields[field_id]
        self._p_changed = 1

    __delitem__ = delField

    security.declareProtected(View, 'getField')
    def getField(self, field_id, default=None):
        """ return a field """
        try:
            return self._fields[field_id]
        except KeyError:
            return default

    __getitem__ = get = getField

    def hasField(self, field_id):
        """ do we have a field with this id?"""
        return field_id in self._names

    has_key = hasField

    security.declareProtected(View, 'searchable')
    def searchable(self):
        """ Return a list containing names of all searchable fields """
        return [f.getName() for f in self._fields.values()  if f.searchable]
        
            
#    security.declareProtected(View, 'fields')
    def fields(self):
        """ return the fields """
        return [self._fields[k] for k in self._names]

    security.declareProtected(View, 'toString')
    def toString(self):
        s = '%s: {' % self.__class__.__name__
        for f in self.fields():
            s = s + '%s,' % (f.toString())
        s = s + '}'
        return s

    security.declareProtected(View, 'signature')
    def signature(self):
        from md5 import md5
        return md5(self.toString()).digest()

InitializeClass(Schemata)


class Schema(Schemata, DefaultLayerContainer):
    """ The Schema """

    __implement__ = (ILayerRuntime, ILayerContainer)

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    _properties = {
        'marshall' : None
        }

    def __init__(self, *args, **kwargs):
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

    security.declareProtected(ModifyPortalContent, 'copy')
    def copy(self):
        """ copy """

        s = Schema()
        for name in self._names:
            s.addField(self._fields[name])
        return s

    security.declareProtected(ModifyPortalContent, 'setDefaults')
    def setDefaults(self, instance):
        """Only call during object initialization. Sets fields to
        schema defaults
        """
        ## XXX think about layout/vs dyn defaults
        for field in self._fields.values():
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

    security.declareProtected(ModifyPortalContent, 'initializeLayers')
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

#    security.declareProtected(View, 'getSchemataNames')
    def getSchemataNames(self):
        """ return name of schematas """
        l = []
        for name in self._names:
            field = self._fields[name]
            if not field.schemata in l:
                l.append(field.schemata)
        return l

#    security.declareProtected(View, 'getSchemataFields')
    def getSchemataFields(self, schemata_name):
        """ return fields of a given schemata """

        l = []
        for name in self._names:
            field = self._fields[name]
            if field.schemata == schemata_name:
                l.append(field)
        return l
        
    security.declareProtected(View, 'validate')
    def validate(self, instance, REQUEST=None, errors=None, data=None, metadata=None):
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
            label = field.widget.Label(instance)
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
                    errors[name] =  translate(
                        'archetypes', 'error_required',
                        {'name': label}, instance,
                        default = "%s is required, please correct."
                        % label,
                        )
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
                        errors[name] = translate(
                            'archetypes', 'error_vocabulary',
                            {'val': val, 'name': label}, instance,
                            default = "Value %s is not allowed for vocabulary "
                            "of element %s." % (val, label),
                            )

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

    ######################################################################
    # Schema manipulation methods 
    ######################################################################

    security.declareProtected(ModifyPortalContent, 'delSchemata')
    def delSchemata(self, schemata_name):
        names = [f.getName() for f in self._fields.values()  if f.schemata==schemata_name]
        for name in names: self.delField(name)

    security.declareProtected(ModifyPortalContent, 'addSchemata')
    def addSchemata(self, name):
        """ create a new schema by adding a new field with schemata 'name' """
        from Products.Archetypes.Field import StringField

        if name in self.getSchemataNames():
            raise ValueError('Schemata "%s" already exists' % name)
        self.addField(StringField('%s_default' % name, schemata=name))

    security.declareProtected(ModifyPortalContent, 'changeSchemataForField')
    def changeSchemataForField(self, fieldname, schemataname):
        """ change the schemata for a field """
        field = self._fields[fieldname]
        self.delField(fieldname)
        field.schemata = schemataname
        self.addField(field)

    security.declareProtected(ModifyPortalContent, 'moveSchemata')
    def moveSchemata(self, name, direction):
        """ move a schemata to left (direction=-1) or to right
            (direction=1)
        """
        if not direction in (-1, 1):
            raise ValueError('direction must be either -1 or 1')

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

        self.clear()

        for s_name in schemata_names:
            for f in fields:
                if f.schemata == s_name:
                    self.addField(f)

    security.declareProtected(ModifyPortalContent, 'moveField')
    def moveField(self, name, direction):
        """ move a field inside a schema to left (direction=-1) or to right
            (direction=1)
        """
        if not direction in (-1, 1):
            raise ValueError('direction must be either -1 or 1')

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

        self.clear()
        for s_name in schemata_names:
            for f in d[s_name]:
                self.addField(f)

    security.declareProtected(ModifyPortalContent, 'replaceField')
    def replaceField(self, name, field):
        """ replace field with name 'name' in-place with 'field' """

        if IField.isImplementedBy(field):
            if not name in self._names:
                raise ValueError("Field '%s' does not exist" % field.getName())
            self._fields[name] = field
        else:
            raise ValueError('wrong field: %s' % field)

InitializeClass(Schema)



# Reusable instance for MetadataFieldList
MDS = MetadataStorage()

class MetadataSchema(Schema):
    """Schema that enforces MetadataStorage."""

    security = ClassSecurityInfo()

    security.declareProtected(ModifyPortalContent,
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

FieldList = Schema
MetadataFieldList = MetadataSchema
