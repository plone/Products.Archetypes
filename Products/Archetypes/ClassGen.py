from __future__ import nested_scopes
import os, os.path
import re

from Products.Archetypes.debug import log
from Products.Archetypes.utils import pathFor, unique, capitalize

from Acquisition import ImplicitAcquisitionWrapper
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from new import instancemethod

_modes = {
    'r' : { 'prefix'   : 'get',
            'attr'     : 'accessor',
            'security' : 'read_permission',
            },
    'm' : { 'prefix'   : 'getRaw',
            'attr'     : 'edit_accessor',
            'security' : 'write_permission',
            },
    'w' : { 'prefix'   : 'set',
            'attr'     : 'mutator',
            'security' : 'write_permission',
            },

    }

class GeneratorError(Exception):
    pass

class Generator:
    def computeMethodName(self, field, mode):
        if mode not in _modes.keys():
            raise TypeError("Unsupported Mode %s in field: %s (%s)" % \
                            (field.getName(), mode))

        prefix = _modes[mode]['prefix']
        name   = capitalize(field.getName())
        return "%s%s" % (prefix, name)

    def makeMethod(self, klass, field, mode, methodName, inst):
        name = field.getName()
        method = None
        target = klass
        if inst: target = inst
            
        if mode == "r":
            def generatedAccessor(self, **kw):
                """Default Accessor."""
                if kw.has_key('schema'):
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].get(self, **kw)
            method = generatedAccessor
        elif mode == "m":
            def generatedEditAccessor(self, **kw):
                """Default Edit Accessor."""
                if kw.has_key('schema'):
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].getRaw(self, **kw)
            method = generatedEditAccessor
        elif mode == "w":
            def generatedMutator(self, value, **kw):
                """Default Mutator."""
                if kw.has_key('schema'):
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].set(self, value, **kw)
            method = generatedMutator
        else:
            raise GeneratorError("""Unhandled mode for method creation:
            %s:%s -> %s:%s""" %(klass.__name__,
                                name,
                                methodName,
                                mode))

        method = instancemethod(method, inst, klass)
        setattr(target, methodName, method)
        return method
    
class ClassGenerator:
    def updateSecurity(self, klass, field, mode, methodName):
        if not hasattr(klass, "security"):
            security = klass.security = ClassSecurityInfo()
        else:
            security = klass.security

        perm = _modes[mode]['security']
        perm = getattr(field, perm, None)
        security.declareProtected(perm, methodName)

    def generateName(self, klass):
        return re.sub('([a-z])([A-Z])', '\g<1> \g<2>', klass.__name__)

    def generateClass(self, klass):
        #We are going to assert a few things about the class here
        #before we start, set meta_type, portal_type based on class
        #name
        klass.meta_type = klass.__name__
        klass.portal_type = klass.__name__
        klass.archetype_name = getattr(klass, 'archetype_name',
                                       self.generateName(klass))

        fields = klass.schema.fields()
        self.generateMethods(klass, fields)

    def generateMethods(self, klass, fields, inst=None):
        generator = Generator()
        for field in fields:
            assert not 'm' in field.mode, 'm is an implicit mode'

            #Make sure we want to muck with the class for this field
            if "c" not in field.generateMode: continue
            for mode in field.mode: #(r, w)
                self.handle_mode(klass, generator, field, mode, inst)
                if mode == 'w':
                    self.handle_mode(klass, generator, field, 'm', inst)

        InitializeClass(klass)

    def handle_mode(self, klass, generator, field, mode, inst):
        attr = _modes[mode]['attr']
        # Did the field request a specific method name?
        methodName = getattr(field, attr, None)
        target = klass
        if inst: target = inst
        
        if not methodName:
            methodName = generator.computeMethodName(field, mode)
            #Now does this exist on target?
            if not hasattr(target, methodName):
                methodName = None # fallback to default field impl
            
        #Note on the class what we did
        attr = _modes[mode]['attr']
        setattr(field, attr, methodName)

def generateCtor(type, module):
    name = capitalize(type)
    ctor = """
def add%s(self, id, **kwargs):
    o = %s(id)
    self._setObject(id, o)
    o = getattr(self, id)
    o.initializeArchetype(**kwargs)
    return id
""" % (name, type)

    exec ctor in module.__dict__
    return getattr(module, "add%s" % name)


_cg = ClassGenerator()
generateClass = _cg.generateClass
generateMethods = _cg.generateMethods
