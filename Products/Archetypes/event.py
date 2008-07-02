"""Event definitions
"""

from zope.interface import implements

from zope.component.interfaces import ObjectEvent
from zope.lifecycleevent import ObjectModifiedEvent

from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IEditBegunEvent
from Products.Archetypes.interfaces import IEditCancelledEvent

# Modification

class ObjectInitializedEvent(ObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """
    implements(IObjectInitializedEvent)

class ObjectEditedEvent(ObjectModifiedEvent):
    """An object is being edited, i.e. modified after the first save
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