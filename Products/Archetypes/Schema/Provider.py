from Acquisition import aq_inner, aq_parent
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.Schema import Schema, SchemaSource, ArchetypesCollectionPolicy

from Acquisition import Implicit
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Schema.Editor import SchemaEditor
from Persistence import Persistent
from ZODB.PersistentMapping import PersistentMapping

from types import StringTypes, ListType, TupleType
import md5


class SchemaProvider(Persistent):
    ## This is the base mixin that allows for schema composites

    def __init__(self):
        self._schemaPolicy = ArchetypesCollectionPolicy()
        self._schemaCache = PersistentMapping()

    ## Schema Provider Hooks
    ##
    def getSchemaEditor(self):
        """override if you need an enhanced editor"""
        return SchemaEditor(self.Schema(), self)


    def _getSchemaCache(self):
        return self._schemaCache

    def _getSchema(self):
        """return the schema associated with this instance"""
        # PHASE: Collect
        # using the policy
        schemaSources = self._schemaPolicy.collect(self)
        ### XXX Each axis should hand back a token that we can
        ## resubmit to validate our cache, but I will punt now
        ## and do full composite. Fake something for now
        if self._schemaPolicy.validate(self, schemaSources):
            return self.schema

        # PHASE: Composite
        # we cache to avoid doing this...
        # this should also keep the relative ordering of fields
        schema = self._schemaPolicy.compose(self, schemaSources)
        # PHASE: Cache
        cache = self._getSchemaCache()
        for source in schemaSources:
            cache[source.axis.getId()] = source.axis.timestamp

        self.schema = schema #we will cache persistently
        return schema

    def Schema(self):
        """Public version of Schema"""
        return self._getSchema()
