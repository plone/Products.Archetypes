from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.debug import log
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.utils import className

from Acquisition import aq_base
from Globals import PersistentMapping
from Products.CMFCore.utils import getToolByName

type_map = {'text':'string',
            'datetime':'date',
            'lines':'lines',
            'integer':'int'
            }

_marker = []

class Storage:
    """Basic, abstract class for Storages. You need to implement
    at least those methods"""

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
    """A marker storage class for used for read-only fields."""
    __implements__ = IStorage

class StorageLayer(Storage):
    """Base, abstract StorageLayer. Storages that need to manipulate
    how they are initialized per instance and/or per field must
    subclass and implement those methods"""

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
    """Stores data as an attribute of the instance. This is the most
    commonly used storage"""

    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        if not hasattr(aq_base(instance), name):
            raise AttributeError(name)
        return getattr(instance, name)

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        value = aq_base(value)
        setattr(aq_base(instance), name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        try:
            delattr(aq_base(instance), name)
        except AttributeError:
            pass
        instance._p_changed = 1

class ObjectManagedStorage(Storage):
    """Stores data using the Objectmanager interface. It's usually
    used for BaseFolder-based content"""

    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        try:
            return instance._getOb(name)
        except Exception, msg:
            raise AttributeError(msg)

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        value = aq_base(value)
        try:
            instance._delObject(name)
        except (AttributeError, KeyError):
            pass
        instance._setObject(name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        instance._delObject(name)
        instance._p_changed = 1

MetadataStorage = AttributeStorage
##class MetadataStorage(StorageLayer):
##    """Storage used for ExtensibleMetadata. Attributes are stored on
##    a persistent mapping named ``_md`` on the instance."""

##    __implements__ = (IStorage, ILayer)

##    def initializeInstance(self, instance, item=None, container=None):
##        base = aq_base(instance)
##        if not hasattr(base, "_md"):
##            instance._md = PersistentMapping()
##            instance._p_changed = 1

##    def initializeField(self, instance, field):
##        # Check for already existing field to avoid  the reinitialization
##        # (which means overwriting) of an already existing field after a
##        # copy or rename operation
##        base = aq_base (instance)
##        if not base._md.has_key(field.getName()):
##            self.set(field.getName(), instance, field.default)

##    def get(self, name, instance, **kwargs):
##        base = aq_base(instance)
##        try:
##            value = base._md[name]
##        except KeyError, msg:
##            # We are acting like an attribute, so
##            # raise AttributeError instead of KeyError
##            raise AttributeError(name, msg)
##        return value

##    def set(self, name, instance, value, **kwargs):
##        base = aq_base(instance)
##        # Remove acquisition wrappers
##        base._md[name] = aq_base(value)
##        base._p_changed = 1

##    def unset(self, name, instance, **kwargs):
##        base = aq_base(instance)
##        if not hasattr(base, "_md"):
##            log("Broken instance %s, no _md" % instance)
##        else:
##            del base._md[name]
##            base._p_changed = 1

##    def cleanupField(self, instance, field, **kwargs):
##        # Don't clean up the field self to avoid problems with copy/rename. The
##        # python garbarage system will clean up if needed.
##        pass

##    def cleanupInstance(self, instance, item=None, container=None):
##        # Don't clean up the instance self to avoid problems with copy/rename. The
##        # python garbarage system will clean up if needed.
##        pass

class MementoStorage(Storage):
    """Stores the data in a memento which we expect to find in self._target
    where instance is converted into a key into the storage
    
    target.storeMemento(instance, memento)
    target.getMemento(instance)
    
    where typically this will store
    instance.UID() -> {fieldName :value}
    where the dict of f:v pairs is the memento
    """

    __implements__ = IStorage

    def _memento(self, instance):
        # XXX How racey is this really?, sorta last write wins
        mementoName ='_v_%s' % self._target
        inst = aq_base(instance)
        memento = getattr(inst, mementoName, None)
        if memento is None:
            rc = getName(instance, REFERENCE_CATALOG)
            dataContainer = rc.lookupObject(self._target)
            assert dataContainer
            memento = datacContainer.getMemento(instance)
            if not memento:
                memento = PersistentMapping()
                dataContainer.setMemento(instance, memento)
        return memento
    
    def get(self, name, instance, **kwargs):
        m = self._memento(instance)
        return m[name]

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        m = self._memento(instance)
        m[name] = value
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        m = self._memento(instance)
        del m[name]
        instance._p_changed = 1


__all__ = ('ReadOnlyStorage', 'ObjectManagedStorage',
           'MetadataStorage', 'AttributeStorage',)

from Products.Archetypes.Registry import registerStorage

for name in __all__:
    storage = locals()[name]
    registerStorage(storage)
