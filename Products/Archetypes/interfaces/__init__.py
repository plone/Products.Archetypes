"""
This file is here to make the module importable.
"""
from annotations import IATAnnotatable, IATAnnotations
from base import IBaseObject, IBaseContent, IBaseFolder, IBaseUnit
from event import IObjectInitializedEvent, IObjectEditedEvent
from event import IEditBegunEvent, IEditCancelledEvent
from event import IWebDAVObjectInitializedEvent, IWebDAVObjectEditedEvent
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.field import IStringField
from Products.Archetypes.interfaces.field import ITextField
from Products.Archetypes.interfaces.field import IDateTimeField
from Products.Archetypes.interfaces.field import ILinesField
from Products.Archetypes.interfaces.field import IIntegerField
from Products.Archetypes.interfaces.field import IFloatField
from Products.Archetypes.interfaces.field import IFileField
from Products.Archetypes.interfaces.field import IImageField
from Products.Archetypes.interfaces.field import IFixedPointField
from Products.Archetypes.interfaces.field import IReferenceField
from Products.Archetypes.interfaces.field import IComputedField
from Products.Archetypes.interfaces.field import IBooleanField
from field import IFileField, IFieldDefaultProvider
from layer import ILayer, ILayerContainer, ILayerRuntime
from marshall import IMarshall
from metadata import IExtensibleMetadata
from orderedfolder import IOrderedFolder
from referenceable import IReferenceable
from referenceengine import IReference, IContentReference
from referenceengine import IReferenceCatalog, IUIDCatalog
from schema import ISchema, ISchemata, ICompositeSchema
from schema import IBindableSchema, IManagedSchema, IMultiPageSchema
from storage import IStorage, ISQLStorage
from templatemixin import ITemplateMixin
from vocabulary import IVocabulary
from athistoryaware import IATHistoryAware
from archetypetool import IArchetypeTool
from edit import IEditForm
from validator import IObjectPreValidation, IObjectPostValidation
from viewlet import IEditBeforeFieldsets, IEditAfterFieldsets

import zope.deferredimport
zope.deferredimport.deprecated(
    "Please use the canonical interface from OFS. "
    "This alias will be removed in the next major version.",
    IOrderedContainer = 'OFS.interfaces:IOrderedContainer',
    )
