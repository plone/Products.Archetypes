from Products.Archetypes.public import *

content_type = BaseSchema + Schema((
    TextField('body',
              required=1,
              searchable=1,
              default_output_type='text/html',
              allowable_content_types=('text/plain',
                                       'text/restructured',
                                       'text/html',
                                       'application/msword'),
              widget  = RichWidget,
              ),
    ))


class SimpleType(BaseContent):
    """A simple archetype"""
    type = content_type
    
                  
registerType(SimpleType)

