from zope.interface import implements, moduleProvides

from Products.Archetypes.VariableSchemaSupport import VarClassGen

from Products.Archetypes.interfaces import ISchemaRegistry
from Products.Archetypes.interfaces import ISchemaInvalidatedEvent

#
# Registry
#

# Holds loaded schemas, keyed by class. Thus, schemas will be calculated once
# (on first access) and stored in memory. If they are removed from the dict,
# they may be re-calculated. The ISchemaInvalidatedEvent event type can be
# used to invalidate a schema

moduleProvides(ISchemaRegistry)
loadedSchemas={}

def findSchema(klass):
    """Find and return the class' schema from the schema cache.
    
    This will retrieve the schema from a cache if possible, otherwise
    it will return None.
    
    Note that the default event handler for ISchemaInvalidatedEvent will
    invalidate the schema cache, meaning None will be returned.
    """
    return loadedSchemas.get(klass, None)
    
def updateSchema(klass, schema):
    """Update the schema for the given class. Returns the correct schema.
    
    A typical pattern would be:
    
    schema = findSchema(self.__class__)
    if schema is None:
        schema = ...
        schema = updateSchema(self.__class__, schema)
    return schema
    """
    loadedSchemas[klass] = schema
    generator = VarClassGen(schema)
    generator.updateMethods(klass)
    return schema
    
# 
# Events
#
    
class SchemaInvalidatedEvent(object):
    """Event fired when the schema of an Archetypes object using
    IExtensibleSchemaProvider is invalidated.
    """
    implements(ISchemaInvalidatedEvent)
    
    def __init__(self, klass):
        self.klass = klass

def invalidateSchema(event):
    """React to an ISchemaInvalidatedEvent by invalidating the required schema.
    """
    klass = event.klass
    if klass in loadedSchemas:
        del loadedSchemas[klass]