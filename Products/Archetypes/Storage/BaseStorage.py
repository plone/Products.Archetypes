from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.debug import log

from Acquisition import aq_base
from Globals import PersistentMapping

from ExtensionClass import Base
from AccessControl import ClassSecurityInfo
from Products.Archetypes.Registry import setSecurity

_marker = []

#XXX subclass from Base?
class Storage:
    """Basic, abstract class for Storages. You need to implement
    at least those methods"""

    __implements__ = IStorage
    
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

class StorageLayer(Storage):
    """Base, abstract StorageLayer. Storages that need to manipulate
    how they are initialized per instance and/or per field must
    subclass and implement those methods"""

    __implements__ = IStorage, ILayer
    
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
