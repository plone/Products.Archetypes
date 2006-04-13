from Acquisition import ImplicitAcquisitionWrapper
from ExtensionClass import Base
from Products.Archetypes.interfaces import ISchema, IBaseObject
from zope.component import adapts
from zope.interface import implements

class BaseSchemaRetriever(Base):
    """ creates a hot copy of schema as self """
    implements(ISchema)
    adapts(IBaseObject)
    def __init__(self, context):
        self.context = context
        schema = self.lookupSchema(context)
        self.__class__=schema.__class__
        self.__dict__=dict(schema.__dict__)
        self = ImplicitAcquisitionWrapper(self, context)

    def lookupSchema(self, context):
        raise NotImplemented

class InstancePersistentSchema(BaseSchemaRetriever):

    def lookupSchema(self, context):
        return context.schema



