from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from debug import log
from utils import pathFor, unique, capitalize
import os, os.path
import re


_modes = {
    'r' : { 'prefix'   : 'get', 
            'attr'     : 'accessor',
            'security' : 'read_permission',
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
            raise TypeError("Unsupported Mode %s in field: %s (%s)" %(field.name, mode))

        prefix = _modes[mode]['prefix']
        name   = capitalize(field.name)
        return "%s%s" % (prefix, name)

    def makeMethod(self, klass, field, mode, methodName):
        if mode == "r":
            method = lambda self, field=field.name: self.type[field].get(self)
        elif mode == "w":
            method = lambda self, value, field=field.name, **kw: self.type[field].set(self, value, **kw)
        else:
            raise GeneratorError("""Unhandled mode for method creation:
            %s:%s -> %s:%s""" %(klass.__name__,
                                field.name,
                                methodName,
                                mode))

        setattr(klass, methodName, method)
            


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
        klass.archetype_name = getattr(klass, 'archetype_name', self.generateName(klass))
        
        fields = klass.type.fields()
        generator = Generator()            
        for field in fields:
            #Make sure we want to muck with the class for this field
            if "c" not in field.generateMode: continue
            type = getattr(klass, 'type')
            
            for mode in field.mode: #(r, w)
                attr = _modes[mode]['attr']

                # Did the field request a specific method name?
                methodName = getattr(field, attr, None)
                if not methodName:
                    methodName = generator.computeMethodName(field, mode)

                # Avoid name space conflicts
                if not hasattr(klass, methodName):
                    if type.has_key(methodName):
                        raise GeneratorError("There is a conflict"
                        "between the Field(%s) and the attempt" 
                        "to generate a method of the same name on"
                        "class %s" % (
                            methodName,
                            klass.__name__))
                    
                    
                    #Make a method for this klass/field/mode
                    generator.makeMethod(klass, field, mode, methodName)
                    self.updateSecurity(klass, field, mode, methodName)

                    
                #Note on the class what we did (even if the method existed)
                attr = _modes[mode]['attr']
                setattr(field, attr, methodName)
                
        InitializeClass(klass)
                

_cg = ClassGenerator()
generateClass = _cg.generateClass
