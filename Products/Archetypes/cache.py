from zope import interface, component
from zope.annotation import IAnnotations
from persistent.dict import PersistentDict

from Products.Archetypes import interfaces

class TransformCache:
    interface.implements(interfaces.ITransformCache)
    
    def __init__(self, field, instance):
        self.field = field
        self.instance = instance
    
    def getCacheIfExists(self):
        ann = IAnnotations(self.instance)
        transforms_cache = ann.get('Products.Archetypes:transforms-cache', None)
        if transforms_cache is None:
            return
        field_cache = transforms_cache.get(self.field.getName(), None)
        if field_cache is None:
            return

    def getOrCreateCache(self):
        ann = IAnnotations(self.instance)
        transforms_cache = ann.setdefault(
            'Products.Archetypes:transforms-cache', PersistentDict())
        field_cache = transforms_cache.setdefault(self.field.getName(),
                                                  PersistentDict())
        return field_cache

    def clear(self):
        field_cache = self.getCacheIfExists()
        if field_cache is None:
            return
        field_cache.clear()
    
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

