from Products.Archetypes.schemata.composity import CompositeSchema
from Products.Archetypes.schemata.facade import FacadeMetadataSchema
from Products.Archetypes.schemata.schema import BasicSchema
from Products.Archetypes.schemata.schema import Schema
from Products.Archetypes.schemata.schema import WrappedSchema
from Products.Archetypes.schemata.schema import ManagedSchema
from Products.Archetypes.schemata.schema import MetadataSchema
from Products.Archetypes.schemata.schemata import getNames
from Products.Archetypes.schemata.schemata import getSchemata
from Products.Archetypes.schemata.schemata import Schemata
from Products.Archetypes.schemata.schemata import WrappedSchemata
from Products.Archetypes.schemata.schemata import SchemaLayerContainer
from Products.Archetypes.schemata.variable import VariableSchemaSupport

FieldList = Schema
MetadataFieldList = MetadataSchema

__all__ = ('CompositeSchema', 'FacadeMetadataSchema', 'BasicSchema', 'Schema',
    'WrappedSchema', 'ManagedSchema', 'MetadataSchema', 'getNames',
    'getSchemata', 'Schemata', 'WrappedSchemata', 'SchemaLayerContainer',
    'VariableSchemaSupport',
    )
