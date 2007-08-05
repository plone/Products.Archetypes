from zope import interface, component
from zope.annotation import IAnnotations
from persistent.dict import PersistentDict
from UserDict import DictMixin

from Products.Archetypes import interfaces

class TransformCache(DictMixin):
    interface.implements(interfaces.ITransformCache)

    key = 'Products.Archetypes:transforms-cache'
    
    def __init__(self, field, instance):
        self.field = field
        self.instance = instance
    
    def getCacheIfExists(self):
        ann = IAnnotations(self.instance)
        transforms_cache = ann.get(self.key, None)
        if transforms_cache is None:
            return
        field_cache = transforms_cache.get(self.field.getName(), None)
        if field_cache is None:
            return
        return field_cache

    def getOrCreateCache(self):
        ann = IAnnotations(self.instance)
        transforms_cache = ann.setdefault(self.key, PersistentDict())
        field_cache = transforms_cache.setdefault(self.field.getName(),
                                                  PersistentDict())
        return field_cache

    def __getitem__(self, key):
        field_cache = self.getCacheIfExists()
        if field_cache is None:
            return None
        return field_cache[key]
    
    def __setitem__(self, key, value):
        if value is None:
            return
        field_cache = self.getOrCreateCache()
        field_cache[key] = value

    def __delitem__(self, key):
        field_cache = self.getCacheIfExists()
        if field_cache is None:
            raise KeyError(key)
        else:
            del field_cache[key]
    
    def keys(self):
        field_cache = self.getCacheIfExists()
        if field_cache is None:
            return ()
        else:
            return field_cache.keys()
