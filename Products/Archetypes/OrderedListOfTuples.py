
from types import StringType

class OrderedListOfTuples:

    def __init__(self, the_list):
        self._list=the_list

    def getList(self):
        return self._list

    def move_objects_up(self, ids, delta=1):
        """ Move objects with ids up by delta. """
        return self.move_objects_by_positions(ids, -delta)


    def move_objects_down(self, ids, delta=1):
        """ Move objects with ids down by delta. """
        return self.move_objects_by_positions(ids, delta)

    def move_objects_to_top(self, ids):
        """ Move objects with ids to top. """
        return self.move_objects_by_positions(ids, -len(self._list))

    def move_objects_to_bottom(self, ids):
        """ Move objects with ids to bottom. """
        return self.move_objects_by_positions(ids, len(self._list))

    def move_objects_by_positions(self, ids, delta):
        """ Move objects with ids by delta. """

        if type(ids) is StringType:
            ids = (ids,)

        min_position = 0
        counter = 0

        objects = list(self._list)

        obj_dict = {}
        for id, obj in objects:
            obj_dict[id] = obj

        if delta > 0:
            ids = list(ids)
            ids.reverse()
            objects.reverse()

        for id in ids:
            object = obj_dict[id]

            old_position = objects.index((id, object))
            new_position = max( old_position - abs(delta), min_position )

            if new_position == min_position:
                min_position += 1

            if old_position <> new_position:
                objects.remove((id, object))
                objects.insert(new_position, (id, object))
                counter += 1

        if counter > 0:
            if delta > 0:
                objects.reverse()
            self._list = tuple(objects)

        return counter