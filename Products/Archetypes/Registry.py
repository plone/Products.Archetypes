import types

from Products.Archetypes.utils import className
from Products.Archetypes.utils import setSecurity
from Products.Archetypes.ArchetypeTool import listTypes
from Products.Archetypes.interfaces.base import IBaseObject


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
        if name in self.__registry:
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
        default_widget = default_widget or klass._properties.get(
            'widget', None)
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
            if IBaseObject.providedBy(b):
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

fieldDescriptionRegistry = Registry(FieldDescription)
availableFields = fieldDescriptionRegistry.items


def registerField(klass, **kw):
    setSecurity(klass, defaultAccess='allow', objectPermission=None)
    field = FieldDescription(klass, **kw)
    fieldDescriptionRegistry.register(field.id, field)

widgetDescriptionRegistry = Registry(WidgetDescription)
availableWidgets = widgetDescriptionRegistry.items


def registerWidget(klass, **kw):
    setSecurity(klass, defaultAccess='allow', objectPermission=None)
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
            if klass not in self._mapping:
                self._mapping[klass] = {}
            map = self._mapping[klass]
        map[property] = type

    def getType(self, property, klass):
        value = None
        if klass in self._mapping:
            value = self._mapping[klass].get(property, None)
        return value or self._default.get(property, 'not-registered')

propertyMapping = PropertyMapping()
registerPropertyType = propertyMapping.register
getPropertyType = propertyMapping.getType
