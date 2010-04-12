from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema + Schema((
    ReferenceField('link',
                   relationship="A",
                   ),

    ReferenceField('links',
                   multiValued=1,
                   relationship="B"
                   ),

    ReferenceField('adds',
                   widget=ReferenceWidget(addable=1),
                   allowed_types=('Refnode', ),
                   relationship="C",
                   multiValued=1,
                   required=1,
                   ),

    ReferenceField('sortedlinks',
                   multiValued=1,
                   referencesSortable=True,
                   relationship="D"
                   ),

    ))


class Refnode(BaseContent):
    """A simple archetype for testing references. It can point to itself"""
    schema = schema

registerType(Refnode, PKG_NAME)
