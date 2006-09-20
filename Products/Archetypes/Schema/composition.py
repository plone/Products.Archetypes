from Acquisition import aq_base

from zope.interface import implements
from zope.component import adapts, getAdapters

from Products.Archetypes.interfaces import ISchemaComposer
from Products.Archetypes.interfaces import ISchemaProvider
from Products.Archetypes.interfaces import IBaseObject

from Products.Archetypes.Schema import Schema

class DefaultSchemaComposer(object):
    """Compose a schema by looking up all ISchemaProvider adapters,
    ordering them and then letting each one extend the previous.
    """
    
    implements(ISchemaComposer)
    adapts(IBaseObject)
    
    def __init__(self, context):
        self.context = context
        
    def __call__(self):
        providers = [p[1] for p in getAdapters((self.context, self), ISchemaProvider)]
        providers.sort(lambda x, y: cmp(x.order, y.order))
        
        schema = None
        for p in providers:
            schema = p(schema)
            
        return schema
        
class BaseSchemaProvider(object):
    """Return the schema set in context.schema
    """
    
    implements(ISchemaProvider)
    adapts(IBaseObject, ISchemaComposer)
    
    order = 0
    
    def __init__(self, context, composer):
        self.context = context
        self.composer = composer
        
    def __call__(self, current=None):
        schema = getattr(aq_base(self.context), 'schema', Schema())
        if current is not None:
            schema = current + schema
        return schema
            