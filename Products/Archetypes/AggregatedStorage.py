"""
AggregatedStorage for Archetypes

(C) 2004, Andreas Jung & Econtec GmbH, D-90492 Nuernberg, Germany

Released as open-source under the current Archetypes license

$Id$
"""

from time import time
from types import StringType, DictType
from threading import Lock

from Storage import Storage
from Registry import Registry

CACHE_TIMEOUT = 5  # timeout in seconds for cache entries to expire

class AggregatedStorage(Storage):
    """ Implementation of the AggregatedStorage proposal as described in http://plone.org/development/teams/developer/AggregatedStorage """

    def __init__(self, caching=0):
        self._reg_ag = Registry(StringType)  # registry for aggregators
        self._reg_dag = Registry(StringType) # registry for disaggregators
        self.cache = {}                      # map (objId, aggregator) -> (timestamp, result_dict)
        self._caching = caching
        self._lock = Lock()
        
    def __getstate__(self):
        """Override __getstate__ used for copy operations
        
        Required to fix the copy problem with the lock
        """
        state = self.__dict__
        state['_lock'] = None
        return state

    def __setstate__(self, state):
        """Override __setstate__ used for copy operations
        
        Required to fix the copy problem with the lock
        """
        state['_lock'] = Lock()
        self.__dict__.update(state)

    def registerAggregator(self, fieldname, methodname):
        if self._reg_ag.get(fieldname):
            raise KeyError('Aggregator for field "%s" already registered' % fieldname)
        self._reg_ag.register(fieldname, methodname)


    def registerDisaggregator(self, fieldname, methodname):
        if self._reg_dag.get(fieldname):
            raise KeyError('Disaggregator for field "%s" already registered' % fieldname)
        self._reg_dag.register(fieldname, methodname)

    def get(self, name, instance, **kwargs):
        methodname = self._reg_ag.get(name)
        if not methodname:
            raise KeyError('No aggregator registered for field "%s"' % name)
        method = getattr(instance, methodname)
        if not method:
            raise KeyError('Aggregator "%s" for field "%s" not found' % (methodname, name))
        result = method(name, instance, **kwargs)
        if not isinstance(result, DictType):
            raise TypeError('Result returned from an aggregator must be DictType')
        return result[name]

        if self._caching:
            cache_entry = self._cache_get(instance.getId(), methodname)
        else:
            cache_entry = None

        if cache_entry is None:
            method = getattr(instance, methodname)
            if not method:
                raise KeyError('Aggregator "%s" for field "%s" not found' % (methodname, name))
            result = method(name, instance, **kwargs)
            if not isinstance(result, DictType):
                raise TypeError('Result returned from an aggregator must be DictType')

            if self._caching:
                self._cache_put(instance.getId(), methodname, result)

            if not result.has_key(name):
                raise KeyError('result dictionary returned from "%s"'
                               ' does not contain an key for "%s"' % 
                               (methodname, name))
            return result[name]
        else:
            return cache_entry[name]
        
    def set(self, name, instance, value, **kwargs):
        methodname = self._reg_dag.get(name)
        if not methodname:
            raise KeyError('No disaggregator registered for field "%s"' % name)

        method = getattr(instance, methodname)
        if not method:
            raise KeyError('Disaggregator "%s" for field "%s" not found' % (methodname, name))
        if self._caching:
            self._cache_remove(instance.getId(), methodname)
        method(name, instance, value, **kwargs)

    def unset(self, name, instance, **kwargs):
        pass

    ######################################################################
    # A very basic cache implementation to cache the result dictionaries
    # returned by the aggregators
    ######################################################################

    def _cache_get(self, objId, methodname):
        """ retrieve the result dictionary for (objId, methodname) """
        self._lock.acquire()
        entry = self.cache.get((objId, methodname))
        if entry is None: 
            self._lock.release()
            return None
        if time.time() - entry[0] > CACHE_TIMEOUT: 
            del self.cache[(objId, methodname)]
            self._lock.release()
            return None
        self._lock.release()
        return entry[1]

    def _cache_put(self, objId, methodname, result):
        """ store (objId, methodname) : (current_time, result) in cache """
        self._lock.acquire()
        self.cache[(objId, methodname)] = (time.time(), result)
        self._lock.release()

    def _cache_remove(self, objId, methodname):
        """ remove (objId, methodname) from cache """
        
        self._lock.acquire()
        key = (objId, methodname)
        if self.cache.has_key(key):
            del self.cache[key] 
        self._lock.release()

from Registry import registerStorage
registerStorage(AggregatedStorage)
