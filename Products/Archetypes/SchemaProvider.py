from Acquisition import aq_inner, aq_parent
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.Schema import Schema
from Acquisition import Implicit
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Schema.Editor import SchemaEditor


from types import StringTypes, ListType, TupleType
import md5

HIGH_PRIORITY = 1
LOW_PRIORITY  = 10

class SchemaResult(object):
    __slots__ = ('priority', 'schema', 'checksum', 'provider')
    
    def __init__(self, priority=None, schema=None, checksum=None, provider=None):
	self.priority = priority
	self.schema = schema
	self.checksum = checksum
	self.provider = provider
            

class Collector(Implicit):
    """Collect relevent schema providers and trigger them as needed

    The process is
    Get Providers -> providers
    Get Schema for each provider
    return a  schema result set
    """
    name = None

    def getProviders(self, instance, providers=None):
        return providers

    def getSchemas(self, instance):
        providers = self.getProviders(instance)
        results = []
        at = getToolByName(instance, TOOL_NAME)
        self._getSchema(instance, at)
        return results

    def checksum(self, instance):
        providers = self.getProviders(instance)
        return self._checksum([p.schema for p in providers]), providers

    # Utils
    def _checksum(self, schemas):
        if type(schemas) not in (ListType, TupleType):
            schemas = (schemas,)
        ck = md5.new()
        for schema in schemas:
            ck.update(schema.toString())
        return ck.hexdigest()

    def _getSchema(self, provider, tool=None):
        """Get the schema provided by a provider"""
        if tool is None:
            tool = getToolByName(provider, TOOL_NAME)
        return tool.getProvidedSchema(provider) 

    def _defaultSchema(self, instance, providers):
        if providers is None:
            sr = SchemaResult(instance.getSchemaPriority(),
                              instance.schema,
                              self._checksum(instance.schema),
                              instance)
            providers = [sr]
        return providers
    
class SelfCollector(Collector):
    name = "self"
    def getProviders(self, instance, providers=None):
        providers = self._defaultSchema(instance, providers)
        return providers

class TypeCollector(Collector):
    name = "type"
    def getProviders(self, instance, providers=None):
        providers = self._defaultSchema(instance, providers)
        at = getToolByName(instance, TOOL_NAME)
        schema = at.getProvidedSchema(instance.meta_type)
        if schema:
            sr = SchemaResult(LOW_PRIORITY,
                              schema,
                              self._checksum(instance.schema),
                              at)
            providers.insert(0, sr)
            
        return providers
    

class AcquisitionCollector(Collector):
    name = "acquisition"
    def getProviders(self, instance, providers=None):
        providers = self._defaultSchema(instance, providers)
        provider = instance.aq_parent
        schema = self._getSchema(provider)
        if schema:
            providers.insert(0, SchemaResult(provider.getSchemaPriority(),
                                             schema,
                                             self._checksum(schema),
                                             provider))
            # and recurse
            collector = provider.getSchemaCollector()
            collector.getProviders(provider, providers)
            
        return providers

class ContainerCollector(Collector):
    name = "container"
    def getProviders(self, instance, providers=None):
        providers = self._defaultSchema(instance, providers)
        provider = aq_parent(aq_inner(instance))
        schema = self._getSchema(provider)
        if schema:
            providers.insert(0, SchemaResult(provider.getSchemaPriority(),
                                             schema,
                                             self._checksum(schema),
                                             provider))
            # and recurse
            collector = provider.getSchemaCollector()
            collector.getProviders(provider, providers)
            
        return providers
    
class ReferenceCollector(Collector):
    name = "reference"
    def getProviders(self, instance, providers=None):
        providers = self._defaultSchema(instance, providers)

        refs = instance.getRefs(relationship="schema_provider")
        for provider in refs:
            schema = self._getSchema(provider)
            if schema:
                providers.insert(0, SchemaResult(provider.getSchemaPriority(),
                                                 schema,
                                                 self._checksum(schema),
                                                 provider))
                # and recurse
                collector = provider.getSchemaCollector()
                collector.getProviders(provider, providers)
                
        return providers
        
                
class SchemaProvider(Implicit):
    ## This is the base mixin that allows for schema composites

    def __init__(self):
        self._collector = SelfCollector()
        self._schema = None
        self._priority = LOW_PRIORITY
        self._checksum = None
        
    ## Schema Provider Hooks
    ##
    def setSchemaCollector(self, collector):
        if type(collector) in StringTypes:
            at = getToolByName(self, TOOL_NAME)
            collector = at.getSchemaCollector(collector)
            
        self._collector = collector

    def getSchemaCollector(self):
        return self._collector

    def getSchemaPriority(self):
        """
        Elements from this schema will be composited at the associated priority,
        TTW elements should be composited at a lower priority than filesystem based
        schema entries, but this is controlable
        """
        return self._priority

    def setSchemaPriority(self, priority):
        self._priority = int(priority)


    def getSchemaProviders(self):
        """all the schema providers used by this object"""
        collector = self.getSchemaCollector()
        providers = collector.getProviders(self)
        return [p.provider for p in providers]

    def getSchemaEditor(self):
        """override if you need an enhanced editor"""
	return SchemaEditor(self.Schema(), self)

	
    # XXX This might be a call back to classgen, but I want to get
    # rid of that anyway
    def Schema(self):
        """return the schema assocaited with this instance"""
        checksum = None

        # PHASE: Collect
        collector = self.getSchemaCollector()
        schemaSet = list()
        #     PHASE: Cache Interaction
        if self._schema:
            # We have a cached composited Schema, we must validate it
            checksum, schemaSet = collector.checksum(self)
            #print "Schema", checksum, schemaSet, self
            if checksum == self._checksum:
                # cache hit
                return self._schema
        #     PHASE: Real Collection
        # PHASE: Composite
        # we cache to avoid doing this...
        pri = {}
        for sr in schemaSet:
            schema = sr.schema
            for f in sr.schema.fields():
                pri.setdefault(sr.priority, []).append(f)

        schema = Schema()
        keys = pri.keys()
        keys.sort()
        current_fields = {}
        for level in keys:
            for field in pri[level]:
                if field.getName() not in current_fields:
                    schema.addField(field)
                    current_fields[field.getName()] = True

        # PHASE: Regenerate
	se = SchemaEditor(schema, self)
	se.regen(self)
                
        # PHASE: Cache
        self._schema = schema
        self._checksum = checksum

        return self._schema


        
        
