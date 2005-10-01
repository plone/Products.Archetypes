from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

try:
    from Products.CMFCore.permissions import setDefaultRoles
except ImportError:
    from Products.CMFCore.CMFCorePermissions import setDefaultRoles

from AccessControl import ClassSecurityInfo

schema = BaseSchema + Schema((
    TextField('body',
              required=1,
              searchable=1,
              default_output_type='text/html',
              allowable_content_types=('text/plain',
                                       'text/restructured',
                                       'text/html',
                                       'application/msword'),
              widget  = RichWidget(description="""Enter or upload text for the Body of the document"""),
              ),
    ))


class SimpleType(BaseContent):
    """A simple archetype"""
    schema = schema

registerType(SimpleType, PKG_NAME)

TestView = 'Archetypes Tests: Protected Type View'
setDefaultRoles(TestView, ('Anonymous', 'Manager',))

TestWrite = 'Archetypes Tests: Protected Type Write'
setDefaultRoles(TestWrite, ('Anonymous', 'Manager',))

class SimpleProtectedType(SimpleType):

    security = ClassSecurityInfo()

    attr_security = AttributeValidator()
    security.setDefaultAccess(attr_security)
    # Delete so it cannot be accessed anymore.
    del attr_security

    archetype_name = portal_type = meta_type = 'SimpleProtectedType'
    schema = schema.copy()
    for f in schema.fields():
        f.read_permission = TestView
        f.write_permission = TestWrite

    security.declareProtected(TestView, 'foo')
    def foo(self):
        return 'bar'

registerType(SimpleProtectedType, PKG_NAME)
