from Products.Archetypes.public import *
from Products.Archetypes.Marshall import PrimaryFieldMarshaller

schema = BaseSchema + Schema((
    FileField('body',
              required=1,
              primary=1,
              widget=FileWidget(),
              ),
    ),
      marshall=PrimaryFieldMarshaller())

class SimpleFile(BaseContent):
    """An File (test) type"""
    schema = schema
    archetype_name = "Simple File Type"

registerType(SimpleFile)

