from Products.Archetypes.public import *

schema = BaseSchema + Schema((
    ReferenceField('link',
                   relationship="A",
                   ),

    ReferenceField('links',
                   multiValued=1,
                   relationship="B"
                   ),

    ))


class Refnode(BaseContent):
    """A simple archetype for testing references. It can point to itself"""
    schema = schema

registerType(Refnode)
