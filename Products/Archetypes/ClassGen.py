import logging
import re
from types import FunctionType as function

from App.class_init import InitializeClass
from Products.Archetypes.log import log
from Products.Archetypes.utils import capitalize
from Products.Archetypes.utils import _getSecurity

# marker that AT should generate a method -- used to discard unwanted
#  inherited methods
AT_GENERATE_METHOD = []


_modes = {
    'r': {'prefix': 'get',
          'attr': 'accessor',
          'security': 'read_permission',
          },
    'm': {'prefix': 'getRaw',
          'attr': 'edit_accessor',
          'security': 'write_permission',
          },
    'w': {'prefix': 'set',
          'attr': 'mutator',
          'security': 'write_permission',
          },
}


class GeneratorError(Exception):
    pass


class Generator:

    def computeMethodName(self, field, mode):
        if mode not in _modes.keys():
            raise TypeError("Unsupported Mode %s in field: %s (%s)" %
                            (field.getName(), mode))

        prefix = _modes[mode]['prefix']
        name = capitalize(field.getName())
        return "%s%s" % (prefix, name)

    def makeMethod(self, klass, field, mode, methodName):
        name = field.getName()
        method = None
        if mode == "r":
            def generatedAccessor(self, **kw):
                # Default Accessor.
                if 'schema' in kw:
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].get(self, **kw)
            method = generatedAccessor
        elif mode == "m":
            def generatedEditAccessor(self, **kw):
                # Default Edit Accessor.
                if 'schema' in kw:
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].getRaw(self, **kw)
            method = generatedEditAccessor
        elif mode == "w":
            def generatedMutator(self, value, **kw):
                # Default Mutator.
                if 'schema' in kw:
                    schema = kw['schema']
                else:
                    schema = self.Schema()
                    kw['schema'] = schema
                return schema[name].set(self, value, **kw)
            method = generatedMutator
        else:
            raise GeneratorError("""Unhandled mode for method creation:
            %s:%s -> %s:%s""" % (klass.__name__,
                                 name,
                                 methodName,
                                 mode))

        # Zope security requires all security protected methods to have a
        # function name. It uses this name to determine which roles are allowed
        # to access the method.
        # This code is renaming the internal name from e.g. generatedAccessor to
        # methodName.
        method = function(method.func_code,
                          method.func_globals,
                          methodName,
                          method.func_defaults,
                          method.func_closure,
                          )
        setattr(klass, methodName, method)


class ClassGenerator:

    def updateSecurity(self, klass, field, mode, methodName):
        security = _getSecurity(klass)

        perm = _modes[mode]['security']
        perm = getattr(field, perm, None)
        method__roles__ = getattr(klass, '%s__roles__' % methodName, 0)

        # Check copied from SecurityInfo to avoid stomping over
        # existing permissions.
        if security.names.get(methodName, perm) != perm:
            log('The method \'%s\' was already protected by a '
                'different permission than the one declared '
                'on the field. Assuming that the explicit '
                'permission declared is the correct one and '
                'has preference over the permission declared '
                'on the field.' % methodName, level=logging.DEBUG)
        elif method__roles__ is None:
            security.declarePublic(methodName)
        elif method__roles__ == ():
            security.declarePrivate(methodName)
        else:
            security.declareProtected(perm, methodName)

    def generateName(self, klass):
        return re.sub('([a-z])([A-Z])', '\g<1> \g<2>', klass.__name__)

    def checkSchema(self, klass):
        pass

    def generateClass(self, klass):
        # We are going to assert a few things about the class here
        # before we start, set meta_type, portal_type based on class
        # name, but only if they are not set yet
        if (not getattr(klass, 'meta_type', None) or
                'meta_type' not in klass.__dict__.keys()):
            klass.meta_type = klass.__name__
        if (not getattr(klass, 'portal_type', None) or
                'portal_type' not in klass.__dict__.keys()):
            klass.portal_type = klass.__name__
        klass.archetype_name = getattr(klass, 'archetype_name',
                                       self.generateName(klass))

        self.checkSchema(klass)
        fields = klass.schema.fields()
        self.generateMethods(klass, fields)

    def generateMethods(self, klass, fields):
        generator = Generator()
        for field in fields:
            assert not 'm' in field.mode, 'm is an implicit mode'

            # Make sure we want to muck with the class for this field
            if "c" not in field.generateMode:
                continue
            type = getattr(klass, 'schema')
            for mode in field.mode:  # (r, w)
                self.handle_mode(klass, generator, type, field, mode)
                if mode == 'w':
                    self.handle_mode(klass, generator, type, field, 'm')

        InitializeClass(klass)

    def handle_mode(self, klass, generator, type, field, mode):
        attr = _modes[mode]['attr']
        # Did the field request a specific method name?
        methodName = getattr(field, attr, None)
        if not methodName:
            methodName = generator.computeMethodName(field, mode)

        # Avoid name space conflicts
        if not hasattr(klass, methodName) \
                or getattr(klass, methodName) is AT_GENERATE_METHOD:
            if methodName in type:
                raise GeneratorError("There is a conflict "
                                     "between the Field(%s) and the attempt "
                                     "to generate a method of the same name on "
                                     "class %s" % (
                                         methodName,
                                         klass.__name__))

            # Make a method for this klass/field/mode
            generator.makeMethod(klass, field, mode, methodName)

        # Update security regardless of the method being generated or
        # not. Not protecting the method by the permission defined on
        # the field may leave security open and lead to misleading
        # bugs.
        self.updateSecurity(klass, field, mode, methodName)

        # Note on the class what we did (even if the method existed)
        attr = _modes[mode]['attr']
        setattr(field, attr, methodName)


def generateCtor(name, module):
    # self is a App.FactoryDispater, Destination() is the real folder
    ctor = """
def add%(name)s(self, id, **kwargs):
    obj = %(name)s(id)
    self._setObject(id, obj, suppress_events=True)
    obj = self._getOb(id)
    obj.manage_afterAdd(obj, self)
    obj.initializeArchetype(**kwargs)
    return obj.getId()
""" % {'name': name}
    exec ctor in module.__dict__
    return getattr(module, "add%s" % name)


def generateZMICtor(name, module):
    zmi_ctor = """
def manage_add%(name)s(self, id, REQUEST=None):
    ''' Constructor for %(name)s '''
    kwargs = {}
    if REQUEST is not None:
        kwargs = REQUEST.form.copy()
        del kwargs['id']
    id = add%(name)s(self, id, **kwargs)
    obj = self._getOb(id)
    manage_tabs_message = 'Successfully added %(name)s'
    if REQUEST is not None:
        url = obj.absolute_url()
        REQUEST.RESPONSE.redirect(url + '/manage_edit%(name)sForm?manage_tabs_message=' + manage_tabs_message)
    return id
""" % {'name': name}
    exec zmi_ctor in module.__dict__
    return getattr(module, "manage_add%s" % name)


_cg = ClassGenerator()
generateClass = _cg.generateClass
generateMethods = _cg.generateMethods
