AXIS = 0
PRIORITY = 1
POLICY = 2

def priorityCmp(x, y):
    return cmp(x[PRIORITY],  y[PRIORITY])

class SourceSet(list):
    """ A formalization of the collected elements from an axis
     [ (axis, priority/weight, policy), ... ]

     The sets will be iterated in priority order from least to
     greatest where policy gives lower numbers precedence.

     """

    def __init__(self, *args):
        super(SourceSet, self).__init__()
        for arg in args:
            self.add(*arg)

    def add(self, axis, priority, policy):
        self.append([axis, priority, policy])
        self.sort()

    def sort(self, cmp=priorityCmp, reverse=False):
        list.sort(self, cmp, reverse=reverse)

    def __add__(self, other):
        assert isinstance(other, SourceSet)
        result = SourceSet(self)
        for datum in other:
            result.add(*datum)
        return result

    def __iadd__(self, other):
        assert isinstance(other, SourceSet)
        for datum in other:
            self.add(*datum)
        return self

