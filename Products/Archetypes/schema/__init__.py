from Products.Archetypes.schema.composity import CompositeSchema
from Products.Archetypes.schema.fascade import FacadeMetadataSchema
from Products.Archetypes.schema.schema import BasicSchema
from Products.Archetypes.schema.schema import Schema
from Products.Archetypes.schema.schema import WrappedSchema
from Products.Archetypes.schema.schema import ManagedSchema
from Products.Archetypes.schema.schema import MetadataSchema
from Products.Archetypes.schema.schemata import getNames
from Products.Archetypes.schema.schemata import getSchemata
from Products.Archetypes.schema.schemata import Schemata
from Products.Archetypes.schema.schemata import WrappedSchemata
from Products.Archetypes.schema.schemata import SchemaLayerContainer
from Products.Archetypes.schema.variable import VariableSchemaSupport

FieldList = Schema
MetadataFieldList = MetadataSchema

__all__ = ('CompositeSchema', 'FacadeMetadataSchema', 'BasicSchema', 'Schema',
    'WrappedSchema', 'ManagedSchema', 'MetadataSchema', 'getNames',
    'getSchemata', 'Schemata', 'WrappedSchemata', 'SchemaLayerContainer',
    'VariableSchemaSupport',
    )
