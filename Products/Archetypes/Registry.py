import types
import inspect

from Products.Archetypes.utils import className
from Products.Archetypes.ArchetypeTool import listTypes
from Products.Archetypes.interfaces.base import IBaseObject

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from Globals import InitializeClass

from config import DEBUG_SECURITY

def getDoc(klass):
    doc = klass.__doc__ or ''
    return doc

class Registry:

    def __init__(self, allowed_class):
        self.__registry = {}
        self.__allowed_class = allowed_class

    def register(self, name, item):
        if not isinstance(item, self.__allowed_class):
            raise TypeError, "Invalid value for item: %r (should be %r)" % \
                  (item, self.__allowed_class)
        self.__registry[name] = item

    def unregister(self, name):
        if self.__registry.has_key(name):
            del self.__registry[name]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

    def items(self):
        return self.__registry.items()

    def __getitem__(self, name):
        return self.__registry[name]

    def get(self, name, default=None):
        return self.__registry.get(name, default)

class FieldDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, default_widget=None,
                 title='', description=''):
        self.id = className(klass)
        self.klass = klass
        default_widget = default_widget or klass._properties.get('widget', None)
        if default_widget is None:
            raise ValueError, '%r Must have a default_widget' % klass
        if type(default_widget) not in [types.StringType, types.UnicodeType]:
            default_widget = className(default_widget)
        self.default_widget = default_widget
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

    def allowed_widgets(self):
        from Products.Archetypes.Registry import availableWidgets
        widgets = []
        for k, v in availableWidgets():
            if v.used_for is None or \
               self.id in v.used_for:
                widgets.append(k)
        return widgets

    def properties(self):
        from Products.Archetypes.Registry import getPropertyType
        props = []
        for k, v in self.klass._properties.items():
            prop = {}
            prop['name'] = k
            prop['type'] = getPropertyType(k, self.klass)
            prop['default'] = v
            props.append(prop)

        return props

class WidgetDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description='', used_for=()):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)
        self.used_for = used_for

    def properties(self):
        from Products.Archetypes.Registry import getPropertyType
        props = []
        for k, v in self.klass._properties.items():
            prop = {}
            prop['name'] = k
            prop['type'] = getPropertyType(k, self.klass)
            prop['default'] = str(v)
            props.append(prop)

        return props

class ValidatorDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

class StorageDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

def findBaseTypes(klass):
    bases = []
    if hasattr(klass, '__bases__'):
        for b in klass.__bases__:
            if IBaseObject.isImplementedByInstancesOf(b):
                bases.append(className(b))
    return bases

class TypeDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, title='', description='',
                 package='', module=''):
        self.id = className(klass)
        self.klass = klass
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)
        self.package = package
        self.module = module

    def schemata(self):
        from Products.Archetypes.Schema import getSchemata
        # Build a temp instance.
        return getSchemata(self.klass('test'))

    def signature(self):
        # Build a temp instance.
        return self.klass('test').Schema().signature()

    def portal_type(self):
        return self.klass.portal_type

    def read_only(self):
        return 1

    def basetypes(self):
        return findBaseTypes(self.klass)

def _getSecurity(klass, create=True):
    # a Zope 2 class can contain some attribute that is an instance
    # of ClassSecurityInfo. Zope 2 scans through things looking for
    # an attribute that has the name __security_info__ first
    info = vars(klass)
    security = None
    for k, v in info.items():
        if hasattr(v, '__security_info__'):
            security = v
            break
    # Didn't found a ClassSecurityInfo object
    if security is None:
        if not create:
            return None
        # we stuff the name ourselves as __security__, not security, as this
        # could theoretically lead to name clashes, and doesn't matter for
        # zope 2 anyway.
        security = ClassSecurityInfo()
        setattr(klass, '__security__', security)
        if DEBUG_SECURITY:
            print '%s has no ClassSecurityObject' % klass.__name__
    return security

def mergeSecurity(klass):
    # This method looks into all the base classes and tries to
    # merge the security declarations into the current class.
    # Not needed in normal circumstances, but useful for debugging.
    bases = list(inspect.getmro(klass))
    bases.reverse()
    security = _getSecurity(klass)
    for base in bases[:-1]:
        s = _getSecurity(base, create=False)
        if s is not None:
            if DEBUG_SECURITY:
                print base, s.names, s.roles
            # Apply security from the base classes to this one
            s.apply(klass)
            continue
        cdict = vars(base)
        b_perms = cdict.get('__ac_permissions__', ())
        if b_perms and DEBUG_SECURITY:
            print base, b_perms
        for item in b_perms:
            permission_name = item[0]
            security._setaccess(item[1], permission_name)
            if len(item) > 2:
                security.setPermissionDefault(permission_name, item[2])
        roles = [(k, v) for k, v in cdict.items() if k.endswith('__roles__')]
        for k, v in roles:
            name = k[:-9]
            security.names[name] = v

def setSecurity(klass, defaultAccess=None, objectPermission=None):
    """Set security of classes

    * Adds ClassSecurityInfo if necessary
    * Sets default access ('deny' or 'allow')
    * Sets permission of objects
    """
    security = _getSecurity(klass)
    if defaultAccess:
        security.setDefaultAccess(defaultAccess)
    if objectPermission:
        if objectPermission == 'public':
            security.declareObjectPublic()
        elif objectPermission == 'private':
            security.declareObjectPrivate()
        else:
            security.declareObjectProtected(objectPermission)

    InitializeClass(klass)

    if DEBUG_SECURITY:
        if getattr(klass, '__allow_access_to_unprotected_subobjects__', False):
            print '%s: Unprotected access is allowed: %s' % (
                  klass.__name__, klass.__allow_access_to_unprotected_subobjects__)
        for name in klass.__dict__.keys():
            method = getattr(klass, name)
            if name.startswith('_') or type(method) != types.MethodType:
                continue
            if not security.names.has_key(name):
                print '%s.%s has no security' % (klass.__name__, name)
            elif security.names.get(name) is ACCESS_PUBLIC:
                print '%s.%s is public' % (klass.__name__, name)

fieldDescriptionRegistry = Registry(FieldDescription)
availableFields = fieldDescriptionRegistry.items
def registerField(klass, **kw):
    # XXX check me high > low security order.
    #setSecurity(klass, defaultAccess=None, objectPermission=None)
    #setSecurity(klass, defaultAccess=None, objectPermission=CMFCorePermissions.View)
    setSecurity(klass, defaultAccess='allow', objectPermission=None)
    #setSecurity(klass, defaultAccess='allow', objectPermission=CMFCorePermissions.View)
    #setSecurity(klass, defaultAccess='allow', objectPermission='public')
    field = FieldDescription(klass, **kw)
    fieldDescriptionRegistry.register(field.id, field)

widgetDescriptionRegistry = Registry(WidgetDescription)
availableWidgets = widgetDescriptionRegistry.items
def registerWidget(klass, **kw):
    # XXX check me high > low security order.
    #setSecurity(klass, defaultAccess=None, objectPermission=None)
    #setSecurity(klass, defaultAccess=None, objectPermission=CMFCorePermissions.View)

    setSecurity(klass, defaultAccess='allow', objectPermission=None)
    #setSecurity(klass, defaultAccess='allow', objectPermission=CMFCorePermissions.View)
    #setSecurity(klass, defaultAccess='allow', objectPermission='public')
    widget = WidgetDescription(klass, **kw)
    widgetDescriptionRegistry.register(widget.id, widget)

storageDescriptionRegistry = Registry(StorageDescription)
availableStorages = storageDescriptionRegistry.items
def registerStorage(klass, **kw):
    setSecurity(klass, defaultAccess=None, objectPermission=None)
    storage = StorageDescription(klass, **kw)
    storageDescriptionRegistry.register(storage.id, storage)

class TypeRegistry:

    def __init__(self):
        pass

    def items(self):
        return [(className(t['klass']),
                 TypeDescription(t['klass'],
                                 title=t['name'],
                                 package=t['package'],
                                 module=t['module'],
                                 )
                 )
                 for t in listTypes()]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

    def __getitem__(self, name):
        items = self.items()
        for k, v in items:
            if k == name:
                return v
        raise KeyError, name

    def get(self, name, default=None):
        items = self.items()
        for k, v in items:
            if k == name:
                return v
        return default

class ValidatorRegistry:

    def __init__(self):
        from Products.validation import validation
        self.validation = validation

    def register(self,  name, item):
        self.validation.register(item)

    def unregister(self, name):
        self.validation.unregister(name)

    def items(self):
        return [(k, ValidatorDescription(v,
                                         title=v.title,
                                         description=v.description))
                for k, v in self.validation.items()]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

validatorDescriptionRegistry = ValidatorRegistry()
availableValidators = validatorDescriptionRegistry.items
def registerValidator(item, name=''):
    name = name or item.name
    validatorDescriptionRegistry.register(name, item)

typeDescriptionRegistry = TypeRegistry()
availableTypes = typeDescriptionRegistry.items

class PropertyMapping:

    def __init__(self):
        self._default = {}
        self._mapping = {}

    def register(self, property, type, klass=None):
        if not klass:
            map = self._default
        else:
            if not self._mapping.has_key(klass):
                self._mapping[klass] = {}
            map = self._mapping[klass]
        map[property] = type

    def getType(self, property, klass):
        value = None
        if self._mapping.has_key(klass):
            value = self._mapping[klass].get(property, None)
        return value or self._default.get(property, 'not-registered')

propertyMapping = PropertyMapping()
registerPropertyType = propertyMapping.register
getPropertyType = propertyMapping.getType
