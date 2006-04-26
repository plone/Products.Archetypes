from Products.Five import BrowserView
from zope.event import notify
from Acquisition import aq_inner
from Products.Archetypes.events import EditBeginsEvent

class LockingView(BrowserView):
    """
    Provides helper methodes for locking support
    """
    def notifyEditBegins(self):
        """
        """
        print "Fired EditBeginsEvent"
        notify(EditBeginsEvent(aq_inner(self.context)))

