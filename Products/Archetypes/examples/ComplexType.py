from Products.Archetypes.public import *
from Products.Archetypes import Field
from SimpleType import SimpleType

fields = ['ObjectField', 'StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField',
          # 'ReferenceField', 'ComputedField', 'CMFObjectField', 'ImageField'
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
    ))

class ComplexType(SimpleType):
    """A simple archetype"""
    schema = SimpleType.schema + schema
    archetypes_name = "Complex Type"

    def _get_selection_vocab(self):
        return DisplayList((('Test','Test'), ))

    def _get_selection_vocab2(self):
        return DisplayList((('Test','Test'),('Test2','Test2'), ))


registerType(ComplexType)
