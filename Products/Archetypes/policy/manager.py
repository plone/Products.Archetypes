from Persistence import Persistent
from ZODB.PersistentList import PersistentList
from ZODB.PersistentMapping import PersistentMapping
from sourceset import PRIORITY, AXIS, POLICY, SourceSet


class PolicyManager(Persistent):

    def getId(self): return self.__name__
    def setId(self, name): self.__name__ = name

    def collect(self, instance, engine, **qualifiers):
        pass

    def compose(self, instance, engine, **qualifiers):
        pass


    def registerComposer(self, composer):
        """Register a composor"""
        pass

    def getComposer(self, object):
        """Typically this will return something that can compose
        objects of the objects type under a given management strategy
        """
        pass


class ArchetypesPolicyManager(PolicyManager):
    """This is the default policy manager for Archetypes Policy
    Compositing.

    It leans towards allowing dynamic overrides giving slightly more
    control to the site administrators than to the original product
    developers.

    If this is not to your liking register another policy with a
    different priority scheme.
    """
    __name__ = "archetypesPolicyManager"

    def __init__(self):
        self._composers = PersistentList()
        self._axisPriority = PersistentMapping()

    # Specific to this axis manager is the notion of Axis Priority
    # we include functions here to manage this (which can later be
    # bound to a ZMI view for this type)
    def assignAxisPriorities(self, engine, **kwargs):
        # each argument is the name of an axis and the priority that
        # will be assigned to it
        knownAxes = [a.__name__ for a in engine.getAxes()]
        for axis in kwargs:
            if axis not in knownAxes:
                raise ValueError("%s is not a known Axis" % axis)

        self._axisPriority.update(kwargs)


    def collect(self, instance, engine, **qualifiers):
        ## each axis will return a source set, these may have
        ## their own priority information which we want to use as
        ## weights in their own axis
        data = SourceSet()
        for  axisManager in engine._axes.itervalues():
            # This yields the source set from a single axis
            collection = axisManager.collect(instance, **qualifiers)
            for c in collection:
                if c[AXIS] != axisManager:
                    c[AXIS] = axisManager
            data += collection
        return data



    def compose(self, instance, sourceSet, engine, **qualifiers):
        # XXX: static axis priority
        # For a given operation identify the axes that apply
        # for now I am encoding the axes priorities staticly,
        # obviously this can change (and must to support new ones)
        # later axes can override in this model
        # Associate axis priority with the elements of the source set
        for datum in sourceSet:
            # scale the priority within the axis to relative to
            # to the weight
            datum[PRIORITY] = \
                 self._axisPriority.get(datum[AXIS].__name__, 0) + \
                                    (datum[PRIORITY] / 100.0)

        # XXX: depend on the ability of the object to compose in a
        # last write wins fashion for now, this is not good enough
        composer = self.getComposer(sourceSet[0])
        policy, work = composer.compose(sourceSet)

        return policy, work


    def registerComposer(self, composer):
        names = [c.__name__ for c in self._composers]
        if composer.__name__ in names:
            del self._composers[names.index(composer.__name__)]
        self._composers.append(composer)

    def getComposer(self, object):
        for composer in self._composers:
            if composer.interested(object):
                return composer

        raise ValueError("No Composer interested in %r from %r" % (
            object, self))

