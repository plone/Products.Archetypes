from Products.Archetypes.interfaces import ISchema, IBaseObject
from zope.component import adapter
from zope.interface import implementer

@implementer(ISchema)
@adapter(IBaseObject)
def instanceSchemaFactory(context):
    """Default schema adapter factory.

    In BaseObject, the Schema() method will do 'schema = ISchema(self)'. This
    adapter factory is the default, meaning that setting a 'schema' class
    attribute pointing to a schema is the default way of supplying a schema.

    You may override this behaviour by supplying a different adapter. Most
    likely, this will adapt some marker interface you apply to your own
    content type and provide ISchema, e.g.:

      @implementer(ISchema)
      @adapter(IMyObject)
      def mySchemaFactory(context):
          return ...

    The challenge is that the accessors and mutators of the returned schema
    must be available as methods on 'context', with appropriate security
    declarations. When the schema is set in a 'schema' class-attribute, this
    is taken care of by ClassGen. However, if you wish to provide the schema
    with a different adapter, you have three choices:

     1. Provide the accessor and mutator methods explicitly in the class. This
     probably means you will be properly implementing a particular interface,
     which is never a bad thing.

     2. Run Products.Archetypes.VariableSchemaSupport.VarClassGen on the class.
     This will generate the missing methods. However, this may be slow, so
     you may need to implement a marker to ensure it only happens once. (The
     VariableSchemaSupport class attempts to do this, but does it badly and is
     probably not to be relied on). Also note that this effectively precludes
     any site-local or per-instance semantics, since it modifies the global
     class dict.

     3. Add the methods per-instance yourself. This is what the ContentFlavors
     product does, so you may be better off using that.
    """
    return context.schema





