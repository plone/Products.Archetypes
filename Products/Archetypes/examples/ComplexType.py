from Products.Archetypes.public import *
from Products.Archetypes import Field

fields = ['ObjectField', 'StringField', 'MetadataField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField',
          # 'ReferenceField', 'ComputedField', 'CMFObjectField', 'ImageField'
          ]

field_instances = []

for f in fields:
    field_instances.append(getattr(Field, f)(f.lower()))

schema = Schema(tuple(field_instances))

class ComplexType(BaseContent):
    """A simple archetype"""
    schema = schema


registerType(ComplexType)

