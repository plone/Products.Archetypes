import sha

from Products.Archetypes.Field import *
from Products.Archetypes.Widget import *
from Products.Archetypes.Schema import Schemata, WrappedSchemata
from Products.Archetypes.ClassGen import ClassGenerator, Generator
from Products.Archetypes.ClassGen import _modes
from Products.Archetypes.utils import OrderedDict

from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from Globals import InitializeClass

from Products.CMFCore import CMFCorePermissions
from ExtensionClass import Base

class VarClassGen(ClassGenerator):

    def __init__(self, schema):
        self.schema=schema

    def generateClass(self, klass):
        #We are going to assert a few things about the class here
        #before we start, set meta_type, portal_type based on class
        #name
        # Only get the values from the klass and not from it's parent classes
        kdict = vars(klass)
        klass.meta_type = kdict.get('meta_type', klass.__name__)
        klass.portal_type = kdict.get('portal_type', klass.meta_type)
        klass.archetype_name = kdict.get('archetype_name',
                                         self.generateName(klass))

        self.checkSchema(klass)

        fields = self.schema.fields()
        generator = Generator()
        for field in fields:
            assert not 'm' in field.mode, 'm is an implicit mode'

            #Make sure we want to muck with the class for this field
            if "c" not in field.generateMode: continue
            type = getattr(klass, 'type')
            for mode in field.mode: #(r, w)
                self.handle_mode(klass, generator, type, field, mode)
                if mode == 'w':
                    self.handle_mode(klass, generator, type, field, 'm')

        InitializeClass(klass)

schemadict={}

class VariableSchemaSupport(Base):
    """
    Mixin class to support instance-based schemas
    Attention: must be before BaseFolder or BaseContent in
    the inheritance list, e.g:

    class Blorf(VariableSchemaSupport, BaseContent):
        def getSchema():
            return some schema definition...

    """

    security = ClassSecurityInfo()

    security.declareProtected(CMFCorePermissions.View,
                              'Schemata')
    def Schemata(self):
        """Returns an ordered dictionary, which maps all Schemata names to
        fields that belong to the Schemata."""
        schema = self.getAndPrepareSchema()
        schemata = OrderedDict()
        for f in schema.fields():
            sub = schemata.get(f.schemata, WrappedSchemata(name=f.schemata))
            sub.addField(f)
            schemata[f.schemata] = sub.__of__(self)
        return schemata

    security.declareProtected(CMFCorePermissions.View,
                              'Schema')
    def Schema(self):
        schema = self.getAndPrepareSchema()
        # XXX see ClassGen about line 130 for a comment
        #if hasattr(schema, 'wrapped'):
        #    return schema.wrapped(self)
        return ImplicitAcquisitionWrapper(schema, self)

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'getAndPrepareSchema')
    def getAndPrepareSchema(self):
        s = self.getSchema()

        # create a hash value out of the schema
        hash=sha.new(str([f.__dict__ for f in s.values()]) +
                     str(self.__class__)).hexdigest()

        if schemadict.has_key(hash): #ok we had that shema already, so take it
            schema=schemadict[hash]
        else: #make a new one and store it using the hash key
            schemadict[hash]=s
            schema=schemadict[hash]
            g=VarClassGen(schema)
            g.generateClass(self.__class__) #generate the methods

        return schema

    # supposed to be overloaded. here the object can return its own schema
    security.declareProtected(CMFCorePermissions.View,
                              'getSchema')
    def getSchema(self):
        return self.schema

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'setSchema')
    def setSchema(self, schema):
        self.schema=schema

InitializeClass(VariableSchemaSupport)
