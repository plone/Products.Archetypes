import ZODB
from ZODB.PersistentMapping import PersistentMapping
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from interfaces.storage import IStorage
from interfaces.field import IObjectField
from interfaces.layer import ILayer
from debug import log
from config import TOOL_NAME

type_map = {'text':'string',
            'datetime':'date',
            'lines':'lines',
            'integer':'int'
            }

_marker = []

class Storage:
    __implements__ = IStorage

    def getName(self):
        return self.__class__.__name__

    def __repr__(self):
        return "<Storage %s>" % (self.getName())

    def __cmp__(self, other):
        return cmp(self.getName(), other.getName())

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

    def initializeInstance(self, instance, item=None, container=None):
        raise NotImplementedError('%s: initializeInstance' % self.getName())

    def cleanupInstance(self, instance, item=None, container=None):
        raise NotImplementedError('%s: cleanupInstance' % self.getName())

    def initializeField(self, instance, field):
        raise NotImplementedError('%s: initializeField' % self.getName())

    def cleanupField(self, instance, field):
        raise NotImplementedError('%s: cleanupField' % self.getName())

class AttributeStorage(Storage):
    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        if not hasattr(aq_base(instance), name):
            raise AttributeError(name)
        return getattr(instance, name)

    def set(self, name, instance, value, **kwargs):
        setattr(aq_base(instance), name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        try:
            delattr(aq_base(instance), name)
        except AttributeError:
            pass
        instance._p_changed = 1

class ObjectManagedStorage(Storage):
    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        try:
            return instance._getOb(name)
        except Exception, msg:
            raise AttributeError(msg)

    def set(self, name, instance, value, **kwargs):
        try:
            instance._delObject(name)
        except (AttributeError, KeyError):
            pass
        instance._setObject(name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        instance._delObject(name)
        instance._p_changed = 1

class MetadataStorage(StorageLayer):
    __implements__ = (IStorage, ILayer)

    def initializeInstance(self, instance, item=None, container=None):
        base = aq_base(instance)
        if not hasattr(base, "_md"):
            instance._md = PersistentMapping()
            instance._p_changed = 1

    def initializeField(self, instance, field):
        self.set(field.name, instance, field.default)

    def get(self, name, instance, **kwargs):
        base = aq_base(instance)
        try:
            value = base._md[name]
        except KeyError, msg:
            # We are acting like an attribute, so
            # raise AttributeError instead of KeyError
            raise AttributeError(name, msg)
        return value

    def set(self, name, instance, value, **kwargs):
        base = aq_base(instance)
        base._md[name] = value
        base._p_changed = 1

    def unset(self, name, instance, **kwargs):
        base = aq_base(instance)
        if not hasattr(base, "_md"):
            log("Broken instance %s, no _md" % instance)
        else:
            del base._md[name]
            base._p_changed = 1

    def cleanupField(self, instance, field, **kwargs):
        self.unset(field.name, instance)

    def cleanupInstance(self, instance, item=None, container=None):
        base = aq_base(instance)
        del base._md

__all__ = ('ReadOnlyStorage', 'ObjectManagedStorage',
           'MetadataStorage', 'AttributeStorage',)
