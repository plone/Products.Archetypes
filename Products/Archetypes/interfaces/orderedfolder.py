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

import zope.deferredimport
zope.deferredimport.deprecated(
    "Please use the canonical interface from OFS. "
    "This alias will be removed in the next major version.",
    IOrderedContainer = 'OFS.interfaces:IOrderedContainer',
    )
