from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema + Schema((
    TextField('body',
              required=1,
              searchable=1,
              default_output_type='text/html',
              allowable_content_types=('text/plain',
                                       'text/restructured',
                                       'text/html',
                                       'application/msword'),
              widget  = RichWidget(description="""Enter or upload text for the Body of the document"""),
              ),
    ))


class SimpleType(BaseContent):
    """A simple archetype"""
    schema = schema

registerType(SimpleType, PKG_NAME)
