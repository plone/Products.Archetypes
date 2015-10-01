from zope.interface import Interface


class IATHistoryAware(Interface):
    """Archetypes history awareness

    Provide access to older revisions of persistent Archetypes

    """

    def getHistories(max=10):
        """Iterate over at most max historic revisions.

        Yields (object, time, transaction_note, user) tuples, where object
        is an object revision approximating what was committed at that time,
        with the current acquisition context.

        """
