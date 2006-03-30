"""
This file is here to make the module importable.
"""
import Products.Five
from Products.Archetypes import utils
from _base import IBaseObject, IBaseContent, IBaseFolder, IBaseUnit
from _referenceable import IReferenceable
from _field import IField, IObjectField, IImageField, IFileField
from _layer import ILayer, ILayerContainer, ILayerRuntime
from _metadata import IExtensibleMetadata
from _referenceengine import IReference, IContentReference, IReferenceCatalog, IUIDCatalog
from _marshall import IMarshall
from _schema import ISchema, ISchemata, ICompositeSchema, IBindableSchema, IManagedSchema 
from _storage import IStorage, ISQLStorage
from _annotations import IATAnnotatable, IATAnnotations

# BBB

import annotations
import base
import field
import layer
import marshall
import metadata
import referenceable
import referenceengine
import schema
import storage

# generate zope2 interfaces
_m=utils.makeZ3Bridges

_m(annotations, IATAnnotatable, IATAnnotations)
_m(base, IBaseObject, IBaseContent, IBaseFolder, IBaseUnit)
_m(field, IField, IObjectField, IImageField, IFileField)
_m(layer, ILayer, ILayerContainer, ILayerRuntime)
_m(marshall, IMarshall)
_m(metadata, IExtensibleMetadata)
_m(referenceable, IReferenceable)
_m(referenceengine, IReference, IContentReference, IReferenceCatalog, IUIDCatalog)
_m(schema, ISchema, ISchemata, ICompositeSchema, IBindableSchema, IManagedSchema )
_m(storage, IStorage, ISQLStorage)
