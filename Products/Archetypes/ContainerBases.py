from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Acquisition import Implicit, aq_parent
from ComputedAttribute import ComputedAttribute

from Products.Archetypes.public import *
from Products.Archetypes.utils import capitalize, mapply
from Products.Archetypes.ClassGen import _modes
from Products.Archetypes.Schema import Schema
from Products.Archetypes.BaseContent import BaseContentMixin


from Products.StupidArchetype.config import *



class MethodBase(Implicit):

    def __init__(self, name):
        self.name=name

    def func_code(self):
        return self.__call__.im_func.func_code
    func_code = ComputedAttribute(func_code, 1)


class AccessorMethod(MethodBase):
    """Default Accessor."""
    def __call__(self, **kw):
        if kw.has_key('schema'):
            schema = kw['schema']
        else:
            schema = aq_parent(self).Schema()
            kw['schema'] = schema
        return schema[self.name].get(aq_parent(self), **kw)


class EditAccessorMethod(MethodBase):
    """Default EditAccessor."""
    def __call__(self, **kw):
        if kw.has_key('schema'):
            schema = kw['schema']
        else:
            schema = aq_parent(self).Schema()
            kw['schema'] = schema
        return schema[self.name].getRaw(aq_parent(self), **kw)


class MutatorMethod(MethodBase):
    """Default Mutator."""
    def __call__(self, value, **kw):
        if kw.has_key('schema'):
            schema = kw['schema']
        else:
            schema = aq_parent(self).Schema()
            kw['schema'] = schema
        return schema[self.name].set(aq_parent(self), value, **kw)


def computeMethodName(field, mode):
        if mode not in _modes.keys():
            raise TypeError("Unsupported Mode %s in field: %s (%s)" % \
                            (field.getName(), mode))

        prefix = _modes[mode]['prefix']
        name   = capitalize(field.getName())
        return "%s%s" % (prefix, name)


def generateMethods(field, instance):
    for mode in field.mode:
        attr = _modes[mode]['attr']
        methodName = computeMethodName(field, mode)
        name = field.getName()
        method = None
        if mode == "r":
            method = AccessorMethod(name)
            setattr(instance, methodName, method)
            setattr(field, attr, methodName)
            if "m" not in field.mode:
                setattr(field, _modes["m"]['attr'], methodName)
        elif mode == "m":
            method = EditAccessorMethod(name)
            setattr(instance, methodName, method)
            setattr(field, attr, methodName)
        elif mode == "w":
            method = MutatorMethod(name)
            setattr(instance, methodName, method)
            setattr(field, attr, methodName)

        if not hasattr(instance, "security"):
            security = instance.security = ClassSecurityInfo()
        else:
            security = instance.security
        perm = _modes[mode]['security']
        perm = getattr(field, perm, None)
        security.declareProtected(perm, methodName)
        InitializeClass(instance)


def bootstrap(field, instance, field_name, use_description=0):
    widget=field.widget
    if not widget.description or not widget.label:
        name = field.getName()
        if not widget.label:
            widget.label = capitalize(field_name)
        if not widget.description and use_description:
            widget.description = "Enter a value for %s" % self.label



schema = Schema()

class ContainerInstanceBase(BaseContentMixin):
    """\
    ContainerInstanceBase

    Base class that creates instance methods for the schema on
    initialization or when ever generateInstanceClass is called.

    This class can be used as a base for archetypes that should
    work as Container Fields Archetypes or for classes with dynamic
    schemas, for instance an ArchetypesPropertyManager or a template
    based class that gets it's schemas from at template.
    """

    schema = schema
    label=None

    def __init__(self, oid, pre_id=None, label=None, **kwargs):
        BaseContentMixin.__init__(self, oid, **kwargs)
        self.generateInstanceClass(pre_id, oid)
        self.label=label

    def generateInstanceClass(self, pre_id, oid):
        schema=Schema()
        self.orig_id=oid
        self.pre_id=pre_id
        for field in self.__class__.schema.fields():
            field_name=field.getName()
            if pre_id is None:
                name=oid+'_'+field_name
            else:
                name=pre_id+'_'+oid+'_'+field_name
            new_field=field.copy()
            new_field.__name__=name
            bootstrap(new_field, self, field_name)
            generateMethods(new_field, self)
            schema.addField(new_field)
        self.schema=schema

    def getLabel(self):
        return self.label or self.orig_id


    def getValueFor(self, key, **kw):
        """Get value for field."""
        schema = self.Schema()
        key="%s_%s_%s" % (self.pre_id, self.orig_id, key)
        try:
            accessor = schema[key].getAccessor(self)
            value = mapply(accessor, **kw)
            return value
        except:
            raise AttributeError("'%s.getValueFor' has no attribute '%s'" % (self.getId(), key) )

    def getEditValueFor(self, key, **kw):
        """Get edit value for field."""
        schema = self.Schema()
        key="%s_%s_%s" % (self.pre_id, self.orig_id, key)
        try:
            accessor = schema[key].getEditAccessor(self)
            value = mapply(accessor, **kw)
            return value
        except:
            raise AttributeError("'%s.getEditValueFor' has no attribute '%s'" % (self.getId(), key) )


    def setValueFor(self, key, value, **kw):
        """Set value for field."""
        schema = self.Schema()
        key="%s_%s_%s" % (self.pre_id, self.orig_id, key)
        try:
            mutator = schema[key].getMutator(self)
            mapply(mutator, value, **kw)
        except:
            raise AttributeError("'%s.setValueFor' has no attribute '%s'" % (self.getId(), key) )



InitializeClass(ContainerInstanceBase)
