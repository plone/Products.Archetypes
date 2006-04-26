from Products.Archetypes.interfaces import ILock
from zope.interface import implements
## Zope Security
from AccessControl import getSecurityManager
from webdav.LockItem import LockItem


class TTWLock(object):
    """
    """
    implements(ILock)

    def __init__(self, context):
        """
        """
        self.context = context

    def lock(self):
        """
        """
        if self.context.wl_isLocked():
            pass
        else:
            user = getSecurityManager().getUser()
            lock = LockItem(user)
            token = lock.getLockToken()
            self.context.wl_setLock(token, lock)
            #if(self.context )

    def unlock(self):
        """
        """
        if self.context.wl_isLocked():
            self.context.wl_clearLocks()
        else:
            pass
