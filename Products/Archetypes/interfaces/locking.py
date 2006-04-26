from zope.app.event.interfaces import IObjectModifiedEvent
from zope.interface import Interface

class ITTWLockable(Interface):
    """Marker interface to indicate Throught The Web locking support"""

class IEditBeginsEvent(IObjectModifiedEvent):
    """An event that is emitted when an user start working on an object"""

class IEditEndsEvent(IObjectModifiedEvent):
    """An event that is emitted when an user has finished working on an object"""

class ILock(Interface):
    """
    """

    def lock():
        """
        """

    def unlock():
        """
        """
