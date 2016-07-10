from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.log import log
from Products.Archetypes.utils import shasattr

from Acquisition import aq_base
from Persistence import PersistentMapping

from AccessControl import ClassSecurityInfo
from Products.Archetypes.Registry import setSecurity, registerStorage
from zope.interface import implementer

type_map = {'text': 'string',
            'datetime': 'date',
            'lines': 'lines',
            'integer': 'int'
            }

_marker = []


# XXX subclass from Base?
@implementer(IStorage)
class Storage:
    """Basic, abstract class for Storages. You need to implement
    at least those methods"""

    security = ClassSecurityInfo()

    security.declarePublic('getName')

    def getName(self):
        return self.__class__.__name__

    def __repr__(self):
        return "<Storage %s>" % (self.getName())

    def __cmp__(self, other):
        return cmp(self.getName(), other.getName())

    security.declarePrivate('get')

    def get(self, name, instance, **kwargs):
        raise NotImplementedError('%s: get' % self.getName())

    security.declarePrivate('set')

    def set(self, name, instance, value, **kwargs):
        raise NotImplementedError('%s: set' % self.getName())

    security.declarePrivate('unset')

    def unset(self, name, instance, **kwargs):
        raise NotImplementedError('%s: unset' % self.getName())

setSecurity(Storage)


class ReadOnlyStorage(Storage):
    """A marker storage class for used for read-only fields."""

    security = ClassSecurityInfo()


@implementer(IStorage, ILayer)
class StorageLayer(Storage):
    """Base, abstract StorageLayer. Storages that need to manipulate
    how they are initialized per instance and/or per field must
    subclass and implement those methods"""

    security = ClassSecurityInfo()

    security.declarePrivate('initializeInstance')

    def initializeInstance(self, instance, item=None, container=None):
        raise NotImplementedError('%s: initializeInstance' % self.getName())

    security.declarePrivate('cleanupInstance')

    def cleanupInstance(self, instance, item=None, container=None):
        raise NotImplementedError('%s: cleanupInstance' % self.getName())

    security.declarePrivate('initializeField')

    def initializeField(self, instance, field):
        raise NotImplementedError('%s: initializeField' % self.getName())

    security.declarePrivate('cleanupField')

    def cleanupField(self, instance, field):
        raise NotImplementedError('%s: cleanupField' % self.getName())

setSecurity(StorageLayer)


class AttributeStorage(Storage):
    """Stores data as an attribute of the instance. This is the most
    commonly used storage"""

    security = ClassSecurityInfo()

    security.declarePrivate('get')

    def get(self, name, instance, **kwargs):
        if not shasattr(instance, name):
            raise AttributeError(name)
        return getattr(instance, name)

    security.declarePrivate('set')

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        value = aq_base(value)
        setattr(aq_base(instance), name, value)
        instance._p_changed = 1

    security.declarePrivate('unset')

    def unset(self, name, instance, **kwargs):
        try:
            delattr(aq_base(instance), name)
        except AttributeError:
            pass
        instance._p_changed = 1


class ObjectManagedStorage(Storage):
    """Stores data using the Objectmanager interface. It's usually
    used for BaseFolder-based content"""

    security = ClassSecurityInfo()

    security.declarePrivate('get')

    def get(self, name, instance, **kwargs):
        try:
            return instance._getOb(name)
        except Exception, msg:
            raise AttributeError(msg)

    security.declarePrivate('set')

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        value = aq_base(value)
        try:
            instance._delObject(name)
        except (AttributeError, KeyError):
            pass
        instance._setObject(name, value)
        instance._p_changed = 1

    security.declarePrivate('unset')

    def unset(self, name, instance, **kwargs):
        instance._delObject(name)
        instance._p_changed = 1


class MetadataStorage(StorageLayer):
    """Storage used for ExtensibleMetadata. Attributes are stored on
    a persistent mapping named ``_md`` on the instance."""

    security = ClassSecurityInfo()

    security.declarePrivate('initializeInstance')

    def initializeInstance(self, instance, item=None, container=None):
        if not shasattr(instance, "_md"):
            instance._md = PersistentMapping()
            instance._p_changed = 1

    security.declarePrivate('initializeField')

    def initializeField(self, instance, field):
        # Check for already existing field to avoid  the reinitialization
        # (which means overwriting) of an already existing field after a
        # copy or rename operation
        base = aq_base(instance)
        if field.getName() not in base._md:
            self.set(field.getName(), instance, field.getDefault(instance))

    security.declarePrivate('get')

    def get(self, name, instance, **kwargs):
        base = aq_base(instance)
        try:
            value = base._md[name]
        except KeyError, msg:
            # We are acting like an attribute, so
            # raise AttributeError instead of KeyError
            raise AttributeError(name, msg)
        return value

    security.declarePrivate('set')

    def set(self, name, instance, value, **kwargs):
        base = aq_base(instance)
        # Remove acquisition wrappers
        if not hasattr(base, '_md'):
            base._md = PersistentMapping()

        base._md[name] = aq_base(value)
        base._p_changed = 1

    security.declarePrivate('unset')

    def unset(self, name, instance, **kwargs):
        if not shasattr(instance, "_md"):
            log("Broken instance %s, no _md" % instance)
        else:
            del instance._md[name]
            instance._p_changed = 1

    security.declarePrivate('cleanupField')

    def cleanupField(self, instance, field, **kwargs):
        # Don't clean up the field self to avoid problems with copy/rename. The
        # python garbarage system will clean up if needed.
        pass

    security.declarePrivate('cleanupInstance')

    def cleanupInstance(self, instance, item=None, container=None):
        # Don't clean up the instance self to avoid problems with copy/rename. The
        # python garbarage system will clean up if needed.
        pass

__all__ = ('ReadOnlyStorage', 'ObjectManagedStorage',
           'MetadataStorage', 'AttributeStorage',)

for name in __all__:
    storage = locals()[name]
    registerStorage(storage)
