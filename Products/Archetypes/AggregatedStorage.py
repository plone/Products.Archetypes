"""
AggregatedStorage for Archetypes

(C) 2004, Andreas Jung & Econtec GmbH, D-90492 Nürnberg, Germany

Released as open-source under the current Archetypes license

$Id: AggregatedStorage.py,v 1.1.2.1 2004/02/19 09:47:54 ajung Exp $
"""

from time import time
from types import StringType, DictType

from Storage import Storage
from Registry import Registry

CACHE_TIMEOUT = 5  # timeout in seconds for cache entries to expire

class AggregatedStorage(Storage):
    """ Implementation of the AggregatedStorage proposal as described in http://plone.org/development/teams/developer/AggregatedStorage """

    def __init__(self):
		self._reg_ag = Registry(StringType)  # registry for aggregators
		self._reg_dag = Registry(StringType) # registry for disaggregators
		self.cache = {}                      # map (objId, aggregator) -> (timestamp, result_dict)

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

        cache_entry = self._cache_get(instance.getId(), methodname)

        if cache_entry is None:
            method = getattr(instance, methodname)
            if not method:
                raise KeyError('Aggregator "%s" for field "%s" not found' % (methodname, name))
            result = method(name, instance, **kwargs)
            if not isinstance(result, DictType):
                raise TypeError('Result returned from an aggregator must be DictType')

            self._cache_put(instance.getId(), methodname, result)
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
        method(name, instance, value, **kwargs)

    ######################################################################
    # A very basic cache implementation to cache the result dictionaries
    # returned by the aggregators
    ######################################################################

	def _cache_get(self, objId, methodname):
		""" retrieve the result dictionary for (objId, methodname) """
		entry = self.cache.get((objId, methodname))
		if entry is None: return None
		if time.time() - entry[0] > CACHE_TIMEOUT: 
			del self.cache[(objId, methodname)]
			return None
		return entry[1]

	def _cache_put(self, objId, methodname, result):
		""" store (objId, methodname) : (current_time, result) in cache """
		self.cache[(objId, methodname)] = (time.time(), result)


from Registry import registerStorage
registerStorage(AggregatedStorage)
