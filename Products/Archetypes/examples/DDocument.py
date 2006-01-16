from Products.Archetypes.public import *
from Products.Archetypes.TemplateMixin import TemplateMixin


schema = BaseSchema + Schema((
    TextField('teaser',
              searchable=1,
              widget=TextAreaWidget(description="""A short lead-in to the
              article so that we might get people to read the body""", 
                                    label="Teaser",
                                    rows=3)),
    ObjectField('author'),
    
    TextField('body',
              required=1,
              primary=1,
              searchable=1,
              default_output_type='text/html',
              allowable_content_types=('text/restructured',
                                       'text/plain',
                                       'text/html',
                                       'application/msword'),
              widget=RichWidget,
              ),
    
    IntegerField("number",
                 index="FieldIndex",
                 default=42,
                 validators=('isInt',),
                 ),
    
    ImageField('image',
               default_output_type='image/jpeg',
               allowable_content_types=('image/*',),
               widget=ImageWidget),

    )) + TemplateMixin.schema

class DDocument(TemplateMixin, BaseContent):
    """An extensible Document (test) type"""
    schema = schema
    archetype_name = "Demo Doc"
    actions = TemplateMixin.actions
    
                  
registerType(DDocument)

