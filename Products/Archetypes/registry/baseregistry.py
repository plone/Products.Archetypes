import types
import inspect

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from Globals import InitializeClass

from Products.Archetypes.lib.utils import className
from Products.Archetypes.config import DEBUG_SECURITY
from Products.Archetypes.interfaces.base import IBaseObject


def getDoc(klass):
    doc = klass.__doc__ or ''
    return doc

def findBaseTypes(klass):
    bases = []
    if hasattr(klass, '__bases__'):
        for b in klass.__bases__:
            if IBaseObject.isImplementedByInstancesOf(b):
                bases.append(className(b))
    return bases

def _getSecurity(klass, create=True):
    # a Zope 2 class can contain some attribute that is an instance
    # of ClassSecurityInfo. Zope 2 scans through things looking for
    # an attribute that has the name __security_info__ first
    info = vars(klass)
    security = None
    for k, v in info.items():
        if hasattr(v, '__security_info__'):
            security = v
            break
    # Didn't found a ClassSecurityInfo object
    if security is None:
        if not create:
            return None
        # we stuff the name ourselves as __security__, not security, as this
        # could theoretically lead to name clashes, and doesn't matter for
        # zope 2 anyway.
        security = ClassSecurityInfo()
        setattr(klass, '__security__', security)
        if DEBUG_SECURITY:
            print '%s has no ClassSecurityObject' % klass.__name__
    return security

def mergeSecurity(klass):
    # This method looks into all the base classes and tries to
    # merge the security declarations into the current class.
    # Not needed in normal circumstances, but useful for debugging.
    bases = list(inspect.getmro(klass))
    bases.reverse()
    security = _getSecurity(klass)
    for base in bases[:-1]:
        s = _getSecurity(base, create=False)
        if s is not None:
            if DEBUG_SECURITY:
                print base, s.names, s.roles
            # Apply security from the base classes to this one
            s.apply(klass)
            continue
        cdict = vars(base)
        b_perms = cdict.get('__ac_permissions__', ())
        if b_perms and DEBUG_SECURITY:
            print base, b_perms
        for item in b_perms:
            permission_name = item[0]
            security._setaccess(item[1], permission_name)
            if len(item) > 2:
                security.setPermissionDefault(permission_name, item[2])
        roles = [(k, v) for k, v in cdict.items() if k.endswith('__roles__')]
        for k, v in roles:
            name = k[:-9]
            security.names[name] = v

def setSecurity(klass, defaultAccess=None, objectPermission=None):
    """Set security of classes

    * Adds ClassSecurityInfo if necessary
    * Sets default access ('deny' or 'allow')
    * Sets permission of objects
    """
    security = _getSecurity(klass)
    if defaultAccess:
        security.setDefaultAccess(defaultAccess)
    if objectPermission:
        if objectPermission == 'public':
            security.declareObjectPublic()
        elif objectPermission == 'private':
            security.declareObjectPrivate()
        else:
            security.declareObjectProtected(objectPermission)

    InitializeClass(klass)

    if DEBUG_SECURITY:
        if getattr(klass, '__allow_access_to_unprotected_subobjects__', False):
            print '%s: Unprotected access is allowed: %s' % (
                  klass.__name__, klass.__allow_access_to_unprotected_subobjects__)
        for name in klass.__dict__.keys():
            method = getattr(klass, name)
            if name.startswith('_') or type(method) != types.MethodType:
                continue
            if not security.names.has_key(name):
                print '%s.%s has no security' % (klass.__name__, name)
            elif security.names.get(name) is ACCESS_PUBLIC:
                print '%s.%s is public' % (klass.__name__, name)


class Registry:

    def __init__(self, allowed_class):
        self.__registry = {}
        self.__allowed_class = allowed_class

    def register(self, name, item):
        if not isinstance(item, self.__allowed_class):
            raise TypeError, "Invalid value for item: %r (should be %r)" % \
                  (item, self.__allowed_class)
        self.__registry[name] = item

    def unregister(self, name):
        if self.__registry.has_key(name):
            del self.__registry[name]

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

    def items(self):
        return self.__registry.items()

    def __getitem__(self, name):
        return self.__registry[name]

    def get(self, name, default=None):
        return self.__registry.get(name, default)

