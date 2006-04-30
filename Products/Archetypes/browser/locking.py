from Products.Five import BrowserView
from zope.event import notify
from Acquisition import aq_inner
from Products.Archetypes.events import EditBeginsEvent
from Products.Archetypes.events import EditEndsEvent
from AccessControl import getSecurityManager
from Products.Archetypes.interfaces import ILock
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

class LockingView(BrowserView):
    """
    Provides helper methodes for locking support
    """

    def notifyEditBegins(self):
        """
        """
        print "Fired EditBeginsEvent"
        notify(EditBeginsEvent(aq_inner(self.context)))

    def notifyEditEnds(self):
        """
        """
        notify(EditEndsEvent(aq_inner(self.context)))

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

    def getLockInformations(self):
        """
        """
        for lock in self.context.wl_lockValues():
            if not lock.isValid():
                continue # Skip invalid/expired locks
            userid = lock.getCreator()[1]
            lockCreationTime = lock.getModifiedTime()
            mt = getToolByName(self.context, 'portal_membership', None)
            pu = getToolByName(self.context, 'portal_url', None)
            authorPage = "%s/author/%s" % (pu(), userid)
            if mt:
                member = mt.getMemberById(userid)
                if member:
                    creatorFullname = member.getProperty('fullname') or userid
            return {'userid': userid, 'creator':creatorFullname, 'lockCreationTime': lockCreationTime, 'authorPage': authorPage}

    def forceUnlock(self, redirect=True):
        """
        """
        locker = ILock(self.context)
        locker.unlock()
        if redirect:
            self.request.RESPONSE.redirect('%s' % self.context.absolute_url())






