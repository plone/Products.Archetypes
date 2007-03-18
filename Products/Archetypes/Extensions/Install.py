from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Extensions.utils import setupArchetypes
from StringIO import StringIO

def install(self, require_dependencies=1):
    out=StringIO()

    if not hasattr(self, "_isPortalRoot"):
        print >> out, "Must be installed in a CMF Site (read Plone)"
        return

    setupArchetypes(self, out, require_dependencies=require_dependencies)
    print >> out, 'Successfully installed %s' % PKG_NAME

    return out.getvalue()
