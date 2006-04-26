from Products.Five import BrowserView
from zope.event import notify
from Acquisition import aq_inner
from Products.Archetypes.events import EditBeginsEvent
from AccessControl import getSecurityManager

class LockingView(BrowserView):
    """
    Provides helper methodes for locking support
    """
    def notifyEditBegins(self):
        """
        """
        print "Fired EditBeginsEvent"
        notify(EditBeginsEvent(aq_inner(self.context)))

    def isLocked(self):
        """
        """
        if not hasattr(self.context, 'wl_isLocked'):
            return False
        elif self.context.wl_isLocked():
            user_id = getSecurityManager().getUser().getId()
            for lock in self.context.wl_lockValues():
                if not lock.isValid():
                    continue # Skip invalid/expired locks
                creator = lock.getCreator()
                if creator and creator[1] == user_id:
                    return False
            return True
        return False

