from Products.Archetypes.public import *
from Products.Archetypes.TemplateMixin import TemplateMixin


schema = I18NBaseSchema + Schema((
    I18NTextField('teaser',
                  searchable=1,
                  widget=TextAreaWidget(description="""A short lead-in to the
                  article so that we might get people to read the body""", 
                                        label="Teaser",
                                        rows=3)),
    ObjectField('author'),
    
    I18NTextField('body',
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

class I18NDDocument(TemplateMixin, I18NBaseContent):
    """An extensible Document (test) type, with I18Nizable content"""
    schema = schema
    archetype_name = "I18N Demo Doc"
    actions = I18NBaseContent + TemplateMixin.actions
    
                  
registerType(I18NDDocument)

