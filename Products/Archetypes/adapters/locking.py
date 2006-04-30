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
        if self.isLock():
            pass
        else:
            user = getSecurityManager().getUser()
            lock = LockItem(user)
            token = lock.getLockToken()
            self.context.wl_setLock(token, lock)

    def isLock(self):
        return bool(self.context.wl_isLocked())

    def getLockCreator(self):
        if(self.isLock()):
            pass
            

    def unlock(self):
        """
        """
        if self.isLock():
            self.context.wl_clearLocks()
        else:
            pass
