
class TransformCache:

    def __init__(self, context):
        self.context = context

    def _genCacheKey(self, identifier, *args):
        key = identifier
        for arg in args:
            key = '%s_%s' % (key, arg)
        key = key.replace('/', '_')
        key = key.replace('+', '_')
        key = key.replace('-', '_')
        key = key.replace(' ', '_')
        return key

    def setCache(self, key, value):
        context = self.context
        key = self._genCacheKey(key)
        if not hasattr(context, '_v_transform_cache'):
            context._v_transform_cache = {}
        context._v_transform_cache[key] = value
        return key

    def getCache(self, key):
        context = self.context
        key = self._genCacheKey(key)
        if not hasattr(context, '_v_transform_cache'):
            return None
        if not key in context._v_transform_cache.keys():
            return None
        return context._v_transform_cache.get(key, None)



