from Products.Archetypes.public import *
from Products.Archetypes import Field
from SimpleType import SimpleType

fields = ['StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField', 'ImageField'
          # 'ComputedField', 'CMFObjectField', 'ReferenceField'
          ]

field_instances = []

for f in fields:
    field_instances.append(getattr(Field, f)(f.lower()))

schema = Schema(tuple(field_instances) + (
    LinesField('selectionlinesfield1',
               vocabulary='_get_selection_vocab',
               enforceVocabulary=1,
               widget=SelectionWidget(label='Selection'),
               ),
    LinesField('selectionlinesfield2',
               vocabulary='_get_selection_vocab',
               widget=SelectionWidget(label='Selection'),
               ),
    LinesField('selectionlinesfield3',
               vocabulary='_get_selection_vocab2',
               widget=MultiSelectionWidget(label='MultiSelection'),
               ),
    TextField('textarea_appendonly',
              widget=TextAreaWidget( label='TextArea',
                                     append_only=1,),
              ),
    TextField('richtextfield',
              allowable_content_types=('text/plain',
                                       'text/structured',
                                       'text/restructured',
                                       'text/html',
                                       'application/msword'),
              widget=RichWidget(label='rich'),
              ),
    ReferenceField('referencefield',
                   relationship='complextype',
                   widget=ReferenceWidget(addable=1),
                   allowed_types=('ComplexType', ),
                   multiValued=1,
                  ),
    #ReferenceField('reffield1',
    #               relationship='myref1',
    #               widget=InAndOutWidget(label='Ref1')
    #              ),
    #ReferenceField('reffield2',
    #               relationship='myref2',
    #               widget=PicklistWidget(label='Ref1'),
    #              ),
    )) + ExtensibleMetadata.schema

class ComplexType(SimpleType):
    """A simple archetype"""
    schema = SimpleType.schema + schema
    archetype_name = meta_type = "Complex Type"
    portal_type = 'ComplexType'

    def _get_selection_vocab(self):
        return DisplayList((('Test','Test'), ))

    def _get_selection_vocab2(self):
        return DisplayList((('Test','Test'),('Test2','Test2'), ))


registerType(ComplexType)
