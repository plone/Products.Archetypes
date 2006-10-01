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
    
# Validation
    
class IObjectValidatingEvent(Interface):
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
