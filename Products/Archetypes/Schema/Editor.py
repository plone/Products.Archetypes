from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import *
from types import StringTypes
from Products.Archetypes.ClassGen import Generator
from ZODB.POSException import ConflictError


class SchemaEditor(object):
    """An interface to manipulating a schema, given an instance of a schema
    it provides convience methods to manipulate it. Its aware of the schema
    provider layer

    Field Reordering is not important to me now, so I will skip it

    Setting the storage on an entire schema is important
    
    """
    __allow_access_to_unprotected_subobjects__ = 1
    
    def __init__(self, schema, context):
        self.schema = schema
        self.context = context

    def enum(self, method, *args, **kwargs):
        """call a method(field, *, **) on each field"""
        results = []
        for field in self.schema.fields():
            results.append(method(field, *args, **kwargs))
        return results

    def regen(self, instance):
        """regenerate the methods of schema for an instance"""
        import pdb;pdb.set_trace()
        gen = Generator()
        for field in self.schema.fields():
            change = 0
            name = field.getName()
            
            if not field.accessor or not hasattr(instance, field.accessor):
                mn = '_v_%s_accessor' % name
                gen.makeMethod(instance.__class__, field, 'r', mn, instance)
                field.edit_accessor = field.accessor = mn
                change += 1
                
            if not field.mutator or not hasattr(instance, field.mutator):
                mn = '_v_%s_mutator' % name
                gen.makeMethod(instance.__class__, field, 'w', mn, instance)
                field.mutator = mn
                change += 1

            # Check if we need to update our own properties
            if change:
                try:
                    field.get(instance)
                except ConflictError, E:
                    raise
                except:
                    field.set(instance, field.default)

    def getProvidedSchemaForField(self, fieldName):
        """
        given a schema (that may be a composite) resolve the real schema
        that supplied a given field
        """
        at = getToolByName(self.context, TOOL_NAME)
        field = self.schema[fieldName]
        providerUUID = field.provider
        subschema = at.getProvidedSchema(providerUUID)
        return subschema

    def getSchemaEditorForSubSchema(self, fieldName):
        """We only want to manipulate the provider schema"""
        subschema = self.getProvidedSchemaForField(fieldName)
        if not subschema: return None
        return SchemaEditor(subschema, self.context)
    

    #Convience methods
    def assignStorage(self, storage, *args, **kwargs):
        """Assign a new storage to everything in a schema"""

        if type(storage) in StringTypes:
            tool = getToolByName(self.context, 'archetypes_ttw_tool')
            if tool:
                for s in tool.storages():
                    if s.title == storage:
                        storage = s.klass(*args, **kwargs)
                        break
                    
        def setStorage(field, storage=storage):
            field.storage = storage
        self.enum(setStorage)
        
    def assignProvider(self, provider):
        """Assign the provider UUID to each field element"""
        def setProvider(field, provider=provider):
            field.provider = provider
        self.enum(setProvider)
        
    
    # Form interaction
    def process_form(self, data):
        """Process form data,
        this method is tied to the skin and you will need to subclass to change this
        """
        from Products.Archetypes.Registry import widgetDescriptionRegistry as widgets
        from Products.Archetypes.Registry import fieldDescriptionRegistry as fields
        diff_set = {}
        for field in self.schema.fields():
            name = field.getName()
            try:
                fv = data["%s_ftype" % name]
                fw = data["%s_wtype" % name]
                if fv != field.type or fw != field.widget.getType():
                    diff_set[name] = (field, fv, fw)
            except KeyError:
                pass

        ## Apply the diffset
        #import pdb;pdb.set_trace()        
        for name, data in diff_set.iteritems():
            field, fv, fw = data
            widget = field.widget
            f = None
            w = None
            # Lets just blindly mutate this for now
            wd = widgets.get(fw)
            if wd:
                w = wd.klass(label=widget.Label(self.context),
                             description=widget.Description(self.context))
                fd = fields.get(fv)
                if fd:
                    f = fd.klass(field.getName(), widget=w, schemata=field.schemata)
                    # We might want to get the value and call the new mutator here
                    # but this could trigger too much
                    self.schema.replaceField(field.getName(), f)
                    
        #self.regen(self.context)
        self.context._p_changed = 1
        
