from Products.Archetypes.interfaces import ILock

class TTWLock(object):
    """
    """
    implements(ILock)

    def lock(self):
        pass

    def unlock(self):
        pass
