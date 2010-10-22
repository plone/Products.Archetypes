try:
    from hashlib import sha1 as sha
except:
    from sha import new as sha

from Products.Archetypes.ClassGen import ClassGenerator

from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from App.class_init import InitializeClass

from Products.CMFCore import permissions
from ExtensionClass import Base

class VarClassGen(ClassGenerator):
    """A version of ClassGen that is able to generate a class' methods based on
    an explicitly given schema.
    """

    def __init__(self, schema):
        self.schema = schema

    def updateMethods(self, klass):
        """Update the methods of the klass to support a new schema.

        This will re-generate methods.
        """
        self.generateMethods(klass, self.schema.fields())

#
# Instance-specific schemas. Note that Archeypes.Schema.compsition, which
# is used in BaseObject, allows schemas to be composed dynamically on a per-
# class basis, and is much more efficient and flexible (except that it cannot
# do different schemas per-*instance*)
#

schemadict={}

class VariableSchemaSupport(Base):
    """
    Mixin class to support instance-based schemas

    NOTE: This implementation has been found to be quite slow, because the
    hash is expensive to calculate and does not appear to work very well as
    a cache key.

    Attention: must be before BaseFolder or BaseContent in
    the inheritance list, e.g:

    class Blorf(VariableSchemaSupport, BaseContent):
        def getSchema():
            return some schema definition...
    """

    security = ClassSecurityInfo()

    security.declareProtected(permissions.View, 'Schema')
    def Schema(self):
        schema = self.getAndPrepareSchema()
        return ImplicitAcquisitionWrapper(schema, self)

    security.declareProtected(permissions.ManagePortal, 'getAndPrepareSchema')
    def getAndPrepareSchema(self):
        s = self.getSchema()

        # create a hash value out of the schema
        hash=sha(str([f.__dict__ for f in s.values()]) +
                 str(self.__class__)).hexdigest()

        if schemadict.has_key(hash): #ok we had that schema already, so take it
            schema=schemadict[hash]
        else: #make a new one and store it using the hash key
            schemadict[hash]=s
            schema=schemadict[hash]
            g=VarClassGen(schema)
            g.updateMethods(self.__class__) #generate the methods

        return schema

    # supposed to be overloaded. here the object can return its own schema
    security.declareProtected(permissions.View, 'getSchema')
    def getSchema(self):
        return self.schema

    security.declareProtected(permissions.ManagePortal,'setSchema')
    def setSchema(self, schema):
        self.schema=schema

InitializeClass(VariableSchemaSupport)
