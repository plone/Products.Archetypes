import ZODB
from ZODB.PersistentMapping import PersistentMapping
from Products.CMFCore.utils import getToolByName
from interfaces.storage import IStorage
from interfaces.field import IObjectField
from interfaces.layer import ILayer
from debug import log
from config import TOOL_NAME
from AccessControl import ClassSecurityInfo

type_map = {'text':'string',
            'datetime':'date',
            'lines':'lines',
            'integer':'int'
            }

class Storage:
    __implements__ = IStorage

    def getName(self):
        return self.__class__.__name__

    def get(self, name, instance, **kwargs):
        raise NotImplementedError('%s: get' % self.getName())

    def set(self, name, instance, value, **kwargs):
        raise NotImplementedError('%s: set' % self.getName())

    def unset(self, name, instance, **kwargs):
        raise NotImplementedError('%s: unset' % self.getName())

class ReadOnlyStorage(Storage):
    __implements__ = IStorage

class StorageLayer(Storage):
    __implements__ = (IStorage, ILayer)

    def initalizeInstance(self, instance):
        raise NotImplementedError('%s: initalizeInstance' % self.getName())

    def cleanupInstance(self, instance):
        raise NotImplementedError('%s: cleanupInstance' % self.getName())

    def initalizeField(self, instance, field):
        raise NotImplementedError('%s: initalizeField' % self.getName())

    def cleanupField(self, instance, field):
        raise NotImplementedError('%s: cleanupField' % self.getName())
    
class AttributeStorage(Storage):
    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        return getattr(instance, name)

    def set(self, name, instance, value, **kwargs):
        setattr(instance, name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        try:
            delattr(instance, name)
        except AttributeError:
            pass
        instance._p_changed = 1

class ObjectManagedStorage(Storage):
    __implements__ = IStorage
    
    def get(self, name, instance, **kwargs):
        return instance._getOb(name)

    def set(self, name, instance, value, **kwargs):
        try:
            instance._delObject(name)
        except AttributeError:
            pass
        instance._setObject(name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        instance._delObject(name)
        instance._p_changed = 1

class MetadataStorage(StorageLayer):
    __implements__ = (IStorage, ILayer)
    
    def initalizeInstance(self, instance):
        if not hasattr(instance, "_md"):
            instance._md = PersistentMapping()
            instance._p_changed = 1

    def initalizeField(self, instance, field):
        self.set(field.name, instance, field.default)

    def get(self, name, instance, **kwargs):
        try:
            value = instance._md[name]
        except KeyError, msg:
            # We are acting like an attribute, so
            # raise AttributeError instead of KeyError
            raise AttributeError(name, msg)
        return value

    def set(self, name, instance, value, **kwargs):
        instance._md[name] = value
        instance._p_changed = 1
        
    def unset(self, name, instance, **kwargs):
        if not hasattr(instance, "_md"):
            log("Broken instance %s, no _md" % instance)
        else:
            del instance._md[name]
            instance._p_changed = 1

    def cleanupField(self, instance, field, **kwargs):
        self.unset(field.name, instance)

    def cleanupInstance(self, instance):
        del instance._md
