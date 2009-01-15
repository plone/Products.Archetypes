from zope.event import notify

from Acquisition import aq_inner

from Products.Five.browser import BrowserView

from Products.Archetypes.event import EditBegunEvent
from Products.Archetypes.event import EditCancelledEvent

class Lifecycle(BrowserView):
    """Helper functions to trigger lifecycle events from TTW code
    """

    def begin_edit(self):
        """Begin an edit operation
        """
        notify(EditBegunEvent(aq_inner(self.context)))

    def cancel_edit(self):
        """Cancel an edit operation
        """
        notify(EditCancelledEvent(aq_inner(self.context)))
