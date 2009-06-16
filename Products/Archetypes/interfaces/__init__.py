"""
This file is here to make the module importable.
"""
from annotations import IATAnnotatable, IATAnnotations
from base import IBaseObject, IBaseContent, IBaseFolder, IBaseUnit
from event import IObjectInitializedEvent, IObjectEditedEvent
from event import IEditBegunEvent, IEditCancelledEvent
from event import IWebDAVObjectInitializedEvent, IWebDAVObjectEditedEvent
from field import IField, IObjectField, IImageField
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
from viewlet import IEditAfterFieldsets

import zope.deferredimport
zope.deferredimport.deprecated(
    "Please use the canonical interface from OFS. " 
    "This alias will be removed in the next major version.",
    IOrderedContainer = 'OFS.interfaces:IOrderedContainer',
    )
