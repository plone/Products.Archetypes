"""Event-related interfaces
"""

from zope.app.event.interfaces import IObjectEvent
from zope.interface import Interface, Attribute

class IObjectPreValidatingEvent(IObjectEvent):
    """An Archetypes object is being pre-validated.
    """

    REQUEST = Attribute("The REQUEST used for validation.")
    errors = Attribute("The errors dictionary.")

class IObjectPostValidatingEvent(IObjectEvent):
    """An archetypes object is being post-validated.
    """

    REQUEST = Attribute("The REQUEST used for validation.")
    errors = Attribute("The errors dictionary.")