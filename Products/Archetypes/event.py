"""Event definitions
"""

from zope.interface import implements

from zope.component.interfaces import ObjectEvent
from zope.lifecycleevent import ObjectModifiedEvent

from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IWebDAVObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IWebDAVObjectEditedEvent
from Products.Archetypes.interfaces import IEditBegunEvent
from Products.Archetypes.interfaces import IEditCancelledEvent

# Modification

class ObjectInitializedEvent(ObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """
    implements(IObjectInitializedEvent)

class WebDAVObjectInitializedEvent(ObjectInitializedEvent):
    """An object is being initialised via WebDAV
    """
    implements(IWebDAVObjectInitializedEvent)

class ObjectEditedEvent(ObjectModifiedEvent):
    """An object is being edited, i.e. modified after the first save
    """
    implements(IObjectEditedEvent)

class WebDAVObjectEditedEvent(ObjectEditedEvent):
    """An object is being edited via WebDAV
    """
    implements(IWebDAVObjectEditedEvent)

class EditBegunEvent(ObjectEvent):
    """An edit operation was begun
    """
    implements(IEditBegunEvent)

class EditCancelledEvent(ObjectEvent):
    """An edit operation was cancelled
    """
    implements(IEditCancelledEvent)
