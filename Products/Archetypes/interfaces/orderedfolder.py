
from Products.Archetypes.interfaces.interface import Interface

class IOrderedFolder( Interface ):

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

