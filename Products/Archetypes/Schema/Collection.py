from Acquisition import aq_parent, aq_inner, aq_base
from Persistence import Persistent
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import *
from ZODB.PersistentMapping import PersistentMapping
from sets import Set
from types import ListType
from Schema import Schema
from Source import SchemaSource

# Global Strategy Registration Interfaces
_v_strategies = {}

def registerAxisManager(strategy):
    _v_strategies[strategy.__name__] = strategy

def getAxisManager(axis):
    return _v_strategies[axis]

def getAxisManagers():
    return _v_strategies.values()



class CollectionMemento(PersistentMapping):
    """A utility class to always store a sequence (because the
    interface calls for Sets and sets can union sequences

    Generally must return lists of SchemaSources
    """

    def __setitem__(self, name, value):
        if type(value) is not ListType: value = [value]
        PersistentMapping.__setitem__(self, name, value)

    def __getitem__(self, name):
        try:
            value = PersistentMapping.__getitem__(self, name)
        except KeyError:
            value = []
        return value

class CollectionAxisManager(Persistent):
    """A strategy object used to
    Collect Schema along a given axis - indicated by name
    """

    def getId(self):
        return self.__name__
    def setId(self, name):
        self.__name__ = name

    def collect(self, object, memento=None):
        """Collect the Schema for an object along a single
        axis, return a Set([Schema])

        If the register call provided a memento it should be passed into
        this method
        """
        pass


    def register(self, tool=None):
        """
        Called when registered with a portal tool, this method can be
        overridden to return the object that will be used to manage
        cached data for the axis
        """
        return None

    def provide(self, memento, schema, *args, **kwargs):
        """Arrange for a schema to be provided along this axis"""
        pass

    def retract(self, memento, *args, **kwargs):
        """Stop providing a schema along an axis"""
        pass

    def annotate(self, schema, provider):
        """mark a field with enough info to find its provider later"""
        for field in schema.fields():
            field.provider = provider



class NullCollector(CollectionAxisManager):
    """A no-op, used when we want an object to do absolutly nothing"""
    __name__ = "null"
    def collect(self, object, memento=None):
        return Set()


class PortalTypeCollector(CollectionAxisManager):
    """Collect the schema provided for this objects portal type. This is
    effectivly the behavior of Archetypes <=1.3
    """
    __name__ = "portal_type"
    # Objects portal_type -> [Schema]
    def collect(self, object, memento=None):
        portal_type = object.portal_type
        # XXX this is really broken, expose the proper interface
        from Products.Archetypes.ArchetypeTool import listTypes
        # play the tricky game of looking in the AT tools global model
        # level data and pulling the schema
        results = Set()
        for type in listTypes():
            if type['portal_type'] == portal_type:
                results.update(Set([type['schema']]))

        # We also need to check if something else is providing for this
        # type
        if memento.has_key(portal_type):
            results.update(memento[portal_type])

        return results

    def register(self, tool=None):
        return CollectionMemento()

    def provide(self, memento, schema, *args, **kwargs):
        portal_type = kwargs['portal_type']
        provider = (self.getId(), portal_type)
        self.annotate(schema, provider)
        memento[portal_type] = schema



registerAxisManager(PortalTypeCollector)

class InstanceTypeCollector(CollectionAxisManager):
    """Collect schema uniquely associated with an instance"""
    # Instance UUID -> [Schema]
    __name__ = "instance"

    def collect(self, object, memento=None):
        at = getToolByName(object, TOOL_NAME)
        uid = object.UID()

        schemaCache = at._getAxisMemento(self.getId())
        return Set(schemaCache[uid])

    def register(self, tool=None):
        return CollectionMemento()

    def provide(self, memento, schema,  *args, **kwargs):
        uid = kwargs['instance'].UID()
        provider = (self.getId(), uid)
        self.annotate(schema, provider)
        memento[uid] = schema

registerAxisManager(InstanceTypeCollector)

class ReferenceTypeCollector(CollectionAxisManager):
    """Collect Schema Via Direct Reference"""
    # Reference UID -> [Schema]
    __name__ = "reference"
    def collect(self, object, memento=None):
        refs = object.getRefs(relationship="schema_provider")
        results = []
        for ref in refs:
            subset = memento[ref.UID()]
            results.extend(subset)

        return Set(results)

    def register(self, tool=None):
        return CollectionMemento()

    def provide(self, memento, schema, *args, **kwargs):
        instance = kwargs['instance']
        source = kwargs['source']
        uid = source.UID()
        provider = (self.getId(), uid)
        self.annotate(schema, provider)
        instance.addReference(source, relationship="schema_provider")
        memento[uid] = schema


registerAxisManager(ReferenceTypeCollector)

class ContainmentTypeCollector(CollectionAxisManager):
    """Collect Schema via containment ancestry"""
    # Ancestor UID -> [SS]
    __name__ = "containment"

    def collect(self, object, memento=None):
        # Collect each UID up to portal root
        portal_url = getToolByName(object, "portal_url")
        portal_root = portal_url.getPortalObject()
        parent = object # bad bootstrapping name
        results = Set()
        # scan up to and including the portal root
        while 1:
            parent = aq_parent(aq_inner(parent))
            try:
                subset = memento[parent.UID()]
                results.update(Set(subset))

            except (KeyError, AttributeError, TypeError):
                pass

            if parent == portal_root: break
        return results

    def register(self, tool=None):
        return CollectionMemento()

    def provide(self, memento, schema, *args, **kwargs):
        uid = kwargs['instance'].UID()
        provider = (self.getId(), uid)
        self.annotate(schema, provider)
        memento[uid] = schema


registerAxisManager(ContainmentTypeCollector)

class CollectorPolicy(Persistent):
    """
    Determine a set of relevant CollectionAxisManager objects
    Collect a set of Schema
    (optionally) Compose a set of SchemaSources into a single Schema
    """

    def getId(self):
        return self.__name__
    def setId(self, name):
        self.__name__ = name


    def collect(self, object):
        """return Schema Set"""
        pass

    def compose(self, object, sourceSet):
        """return a schema... your schema..."""
        pass



class ArchetypesCollectionPolicy(CollectorPolicy):
    """Given a set of globally registered axies and an Archetypes Tool
    resolve the Schema for each object.

    We also provide the default merge strategy here
    """

    __name__ = "archetype_policy"

    DEFAULT_PRIORITY = 0

    def collect(self, object):
        at = getToolByName(object, TOOL_NAME)
        axisNames = at.getSchemaAxisNames()

        result = Set()

        for axisName in axisNames:
            axis = at.getSchemaAxis(axisName)
            memento = at._getAxisMemento(axisName)
            schemas = axis.collect(object, memento)
            # Create the schema source objects
            for schema in schemas:
                result.add(SchemaSource(axis, schema))
        return result

    def compose(self, object, sourceSet):
        at = getToolByName(object, TOOL_NAME)
        policyInfo = at._getPolicyMemento(self.getId())
        # For this policy we keep axis priority information used to
        # handle the merge in the memento, this allows new axes to be
        # brought into specific sites and handled.
        # Fast path the common case
        if len(sourceSet) == 1:
            schema = sourceSet.pop().schema
        else:
            pri = {}
            for ss in sourceSet:
                schema = ss.schema
                priority = policyInfo.get(ss.axis.getId(),
                                          self.DEFAULT_PRIORITY)
                for f in ss.schema.fields():
                    pri.setdefault(priority, list()).append((f, ss))

            schema = Schema()
            priorityLevels = pri.keys()
            priorityLevels.sort()
            current_fields = {}
            for level in priorityLevels:
                for field, ss in pri[level]:
                    if field.getName() not in current_fields:
                        # XXX if it is in found set we should still look
                        # for accessor/mutator names which may bind to
                        # real methods. In general we don't want to give
                        # up behavior and so we will codify this behavior
                        # as the default.
                        schema.addField(field)
                        current_fields[field.getName()] = True


        return schema
