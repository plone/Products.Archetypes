"""Event-related interfaces
"""

from zope.interface import Interface, Attribute

from zope.component.interfaces import IObjectEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

# Modification

class IObjectInitializedEvent(IObjectModifiedEvent):
    """An object is being initialised, i.e. populated for the first time
    """
    
class IObjectEditedEvent(IObjectModifiedEvent):
    """An object is being edited, i.e. modified after the first save
    """

class IEditBegunEvent(IObjectEvent):
    """An event signalling that editing has begun on an object
    """
    
class IEditCancelledEvent(IObjectEvent):
    """An event signalling that editing was cancelled on the given object
    """
    
# Validation
    
class IObjectValidatingEvent(IObjectEvent):
    """A validation-related event
    """
    
    REQUEST = Attribute("The REQUEST used for validation.")
    errors = Attribute("The errors dictionary.")

class IObjectPreValidatingEvent(IObjectValidatingEvent):
    """An Archetypes object is being pre-validated.
    """

class IObjectPostValidatingEvent(IObjectValidatingEvent):
    """An archetypes object is being post-validated.
    """
