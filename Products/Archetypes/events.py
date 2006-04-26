from Acquisition import aq_base
from zope.interface import implements
from zope.app.event.objectevent import ObjectModifiedEvent
from Products.Archetypes.interfaces import IEditBeginsEvent
from Products.Archetypes.interfaces import IEditEndsEvent
from Products.Archetypes.interfaces import ITTWLockable
from webdav.LockItem import LockItem

## Zope Security
from AccessControl import getSecurityManager

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
    if ITTWLockable.providedBy(obj):
        if obj.wl_isLocked():
            obj.wl_clearLocks()
        else:
            pass

def lockOnEditBegins(obj, event):
    """
    lock the object when a user start working on the object
    """
    if ITTWLockable.providedBy(obj):
        if obj.wl_isLocked():
            pass
        else:
            user = getSecurityManager().getUser()
            lock = LockItem(user)
            token = lock.getLockToken()
            obj.wl_setLock(token, lock)
    else:
        print "locking not supported"
