from Acquisition import Implicit, aq_parent
from Products.CMFCore.utils import _checkPermission as checkPerm
from Products.Archetypes.Storage import AttributeStorage

class AttributeValidator(Implicit):
    """(Ab)Use the security policy implementation.

    This class will be used to protect attributes managed by
    AttributeStorage with the same permission as the accessor method.

    It does so by abusing a feature of the security policy
    implementation that the
    '__allow_access_to_unprotected_subobjects__' attribute can be (0,
    1) or a dictionary of {name: 0|1} or a callable instance taking
    'name' and 'value' arguments.

    The said attribute is accessed through getattr(), so by
    subclassing from Implicit we get the accessed object as our
    aq_parent.

    Next step is to check if the name is indeed a field name, and if
    so, if it's using AttributeStorage, and if so, check the
    read_permission against the object being accessed. All other cases
    return '1' which means allow.
    """

    def __call__(self, name, value):
        context = aq_parent(self)
        schema = context.Schema()
        if not schema.has_key(name):
            return 1
        field = schema[name]
        if not isinstance(field.getStorage(), AttributeStorage):
            return 1
        perm = field.read_permission
        if checkPerm(perm, context):
            return 1
        return 0
