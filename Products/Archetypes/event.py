"""Event definitions
"""

from zope.interface import implements

from zope.component.interfaces import ObjectEvent
from zope.lifecycleevent import ObjectModifiedEvent

from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IEditBegunEvent
from Products.Archetypes.interfaces import IEditCancelledEvent

from Products.Archetypes.interfaces import IObjectValidatingEvent
from Products.Archetypes.interfaces import IObjectPreValidatingEvent
from Products.Archetypes.interfaces import IObjectPostValidatingEvent

# Modification

class ObjectInitializedEvent(ObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """
    implements(IObjectInitializedEvent)

class ObjectEditedEvent(ObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """
    implements(IObjectEditedEvent)

class EditBegunEvent(ObjectEvent):
    """An edit operation was begun
    """
    implements(IEditBegunEvent)
    
class EditCancelledEvent(ObjectEvent):
    """An edit operation was cancelled
    """
    implements(IEditCancelledEvent)

# Validation

class ObjectValidatingEvent(ObjectEvent):
    """Base class for validation events
    """
    implements(IObjectValidatingEvent)
    
    def __init__(self, object, REQUEST, errors):
        super(ObjectValidatingEvent, self).__init__(object) 
        self.REQUEST = REQUEST
        self.errors = errors

class ObjectPreValidatingEvent(ObjectValidatingEvent):
    """An Archetypes object is being pre-validated.
    """
    implements(IObjectPreValidatingEvent)
    
class ObjectPostValidatingEvent(ObjectValidatingEvent):
    """An archetypes object is being post-validated.
    """
    implements(IObjectPostValidatingEvent)