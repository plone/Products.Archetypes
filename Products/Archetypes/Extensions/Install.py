from Products.Archetypes.config import *
from Products.Archetypes.public import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.utils import setupEnvironment
from Products.Archetypes.Extensions.utils import setupArchetypes
from StringIO import StringIO

def install(self, include_demo=None, require_dependencies=1):
    out=StringIO()

    if not hasattr(self, "_isPortalRoot"):
        print >> out, "Must be installed in a CMF Site (read Plone)"
        return
    
    setupArchetypes(self, out, require_dependencies=require_dependencies)

    if include_demo or INSTALL_DEMO_TYPES:
        print >> out, "Installing %s" % listTypes(PKG_NAME)
        installTypes(self, out, listTypes(PKG_NAME), PKG_NAME,
                     require_dependencies=require_dependencies,
                     install_deps=0)
        print >> out, 'Successfully installed the demo types.'

    print >> out, 'Successfully installed %s' % PKG_NAME

    return out.getvalue()

def uninstall(portal):
    prod = getattr(portal.portal_quickinstaller, PKG_NAME)
    prod.portalobjects = [po for po in prod.portalobjects
                          if po[-8:] != '_catalog']
