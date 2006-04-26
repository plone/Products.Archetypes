from Acquisition import aq_base
from zope.interface import implements
from zope.app.event.objectevent import ObjectModifiedEvent
from Products.Archetypes.interfaces import IEditBeginsEvent
from Products.Archetypes.interfaces import IEditEndsEvent
from Products.Archetypes.interfaces import ILock

class EditBeginsEvent(ObjectModifiedEvent):
    """An event that is emitted when an user start working on an object"""
    implements(IEditBeginsEvent)

class EditEndsEvent(ObjectModifiedEvent):
    """An event that is emitted when an user has finished working on an object"""
    implements(IEditEndsEvent)

def unlockAfterModification(obj, event):
    """
    release the DAV lock after save
    """
    locker = ILock(obj)
    locker.unlock()

def lockOnEditBegins(obj, event):
    """
    lock the object when a user start working on the object
    """
    locker = ILock(obj)
    locker.lock()

