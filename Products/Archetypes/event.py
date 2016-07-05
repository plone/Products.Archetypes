"""Event definitions
"""

from zope.interface import implementer

from zope.component.interfaces import ObjectEvent
from zope.lifecycleevent import ObjectModifiedEvent

from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IWebDAVObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IWebDAVObjectEditedEvent
from Products.Archetypes.interfaces import IEditBegunEvent
from Products.Archetypes.interfaces import IEditCancelledEvent

# Modification


@implementer(IObjectInitializedEvent)
class ObjectInitializedEvent(ObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """


@implementer(IWebDAVObjectInitializedEvent)
class WebDAVObjectInitializedEvent(ObjectInitializedEvent):
    """An object is being initialised via WebDAV
    """


@implementer(IObjectEditedEvent)
class ObjectEditedEvent(ObjectModifiedEvent):
    """An object is being edited, i.e. modified after the first save
    """


@implementer(IWebDAVObjectEditedEvent)
class WebDAVObjectEditedEvent(ObjectEditedEvent):
    """An object is being edited via WebDAV
    """


@implementer(IEditBegunEvent)
class EditBegunEvent(ObjectEvent):
    """An edit operation was begun
    """


@implementer(IEditCancelledEvent)
class EditCancelledEvent(ObjectEvent):
    """An edit operation was cancelled
    """
