import types
import inspect

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from Globals import InitializeClass

from Products.Archetypes.lib.utils import className
from Products.Archetypes.config import DEBUG_SECURITY
from Products.Archetypes.interfaces.base import IBaseObject

from Products.Archetypes.registry.baseregistry import getDoc
from Products.Archetypes.registry.baseregistry import findBaseTypes
from Products.Archetypes.registry.baseregistry import setSecurity
from Products.Archetypes.registry.baseregistry import mergeSecurity
from Products.Archetypes.registry.baseregistry import Registry

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
        # Build a temp instance.
        from Products.Archetypes.schema import getSchemata
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
        from Products.Archetypes import listTypes
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
