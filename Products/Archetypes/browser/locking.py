from Products.Five import BrowserView
from zope.event import notify
from Acquisition import aq_inner
from Products.Archetypes.events import EditBeginsEvent
from Products.Archetypes.events import EditEndsEvent
from AccessControl import getSecurityManager
from Products.Archetypes.interfaces import ILock
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from datetime import timedelta

class LockingView(BrowserView):
    """
    Provides helper methodes for locking support
    """

    def notifyEditBegins(self):
        """
        """
        notify(EditBeginsEvent(aq_inner(self.context)))

    def notifyEditEnds(self):
        """
        """
        notify(EditEndsEvent(aq_inner(self.context)))

    def hasLock(self):
        user_id = getSecurityManager().getUser().getId()
        for lock in self.context.wl_lockValues():
            if not lock.isValid():
                continue # Skip invalid/expired locks
            creator = lock.getCreator()
            if creator and creator[1] == user_id:
                return True
        return False

    def isLockedForMe(self):
        """
        """
        if not hasattr(self.context, 'wl_isLocked'):
            return False
        elif self.context.wl_isLocked():
            return not self.hasLock()
        return False

    def getNiceTimeDifference(self, baseTime):
        now=DateTime()
        days = int(round(now-DateTime(baseTime) ))
        delta = timedelta(now-DateTime(baseTime))
        days = delta.days
        hours = int(delta.seconds/3600)
        minutes = (delta.seconds - (hours * 3600))/60
        bylinedate = ""
        if days == 0:
            if hours == 0:
                if delta.seconds < 120:
                    bylinedate = "1 minute"
                else:
                    bylinedate = "%s minutes" % minutes
            elif hours == 1:
                bylinedate = "%s hour and %s minutes" % (hours, minutes)
            else:
                bylinedate = "%s hours and %s minutes" % (hours, minutes)
        else:
            if days == 1:
                bylinedate = "%s day and %s hours" % (days, hours)
            else:
                bylinedate = "%s days and %s hours" % (days, hours)
        return bylinedate

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
            return {'userid': userid, 'creator':creatorFullname,
                    'lockCreationTime': lockCreationTime,
                    'authorPage': authorPage,
                    'timeDifference':self.getNiceTimeDifference(lockCreationTime)
            }

    def forceUnlock(self, redirect=True):
        """
        """
        locker = ILock(self.context)
        locker.unlock()
        if redirect:
            self.request.RESPONSE.redirect('%s' % self.context.absolute_url())

    def safeUnlock(self):
        if(self.hasLock()):
            notify(EditEndsEvent(aq_inner(self.context)))








