from zope.interface import Interface

class IOrderedFolder(Interface):
    """ DEPRECATED, will be removed in next releaese """

    def get_object_position( id ):
        """Return the position of the object.
        """

    def move_object_to_position( id, newpos ):
        """Move object to position.
        """

    def move_object_up( id ):
        """Move object up.
        """

    def move_object_down( id ):
        """Move object down.
        """

    def move_object_to_top( id ):
        """Move object to top.
        """

    def move_object_to_bottom( id ):
        """Move object to bottom.
        """



# this interface is needed while Archetypes isnt dependend on Zope 2.7
# if it depends on it should be replaced by importing
# http://cvs.zope.org/Packages/OFS/IOrderSupport.py
# instead of this class.
class IOrderedContainer(Interface):
    """ Ordered Container interface.

    This interface provides a common mechanism for maintaining ordered
    collections.
    """

    def moveObjectsByDelta(ids, delta, subset_ids=None):
        """ Move specified sub-objects by delta.

        If delta is higher than the possible maximum, objects will be moved to
        the bottom. If delta is lower than the possible minimum, objects will
        be moved to the top.

        If subset_ids is not None, delta will be interpreted relative to the
        subset specified by a sequence of ids. The position of objects that
        are not part of this subset will not be changed.

        The order of the objects specified by ids will always be preserved. So
        if you don't want to change their original order, make sure the order
        of ids corresponds to their original order.

        If an object with id doesn't exist an error will be raised.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsUp(ids, delta=1):
        """ Move specified sub-objects up by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsDown(ids, delta=1):
        """ Move specified sub-objects down by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToTop(ids):
        """ Move specified sub-objects to top of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToBottom(ids):
        """ Move specified sub-objects to bottom of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def orderObjects(key, reverse=None):
        """ Order sub-objects by key and direction.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def getObjectPosition(id):
        """ Get the position of an object by its id.

        Permission -- Access contents information

        Returns -- Position
        """
