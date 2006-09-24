from Products.Archetypes.interfaces import ISchema, IBaseObject
from zope.component import adapter
from zope.interface import implementer

@implementer(ISchema)
@adapter(IBaseObject)
def instanceSchemaFactory(context):
    return context.schema





