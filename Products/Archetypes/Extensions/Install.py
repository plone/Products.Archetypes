from Products.Archetypes.config import *
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.utils import setupEnvironment
from Products.Archetypes.Extensions.utils import setupArchetypes
from StringIO import StringIO

from zope.interface import directlyProvides
from zope.app.component.hooks import setSite, setHooks
from zope.app import zapi
from archetypes.uid.interfaces import IUIDQuery
from archetypes.uid.at.query import UIDQuery

from Products.Five.site.localsite import enableLocalSiteHook
from zope.app.component.hooks import setSite, setHooks

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

    try:
        installUtilities(self, out)
    except Exception, e: #%/$"!
        print ("* %s *" % e) * 3

    print >> out, 'Successfully installed %s' % PKG_NAME

    return out.getvalue()

def uninstall(portal):
    prod = getattr(portal.portal_quickinstaller, PKG_NAME)
    prod.portalobjects = [po for po in prod.portalobjects
                          if po[-8:] != '_catalog']

def installUtilities(portal, out):
    # XXX  this is getting called twice when we test
    enableLocalSiteHook(portal)
    setSite(portal)
    setHooks()

    from archetypes.uid.interfaces import IUIDQuery
    from archetypes.uid.at.query import UIDQuery

    try:
        portal.getSiteManager().registerUtility(
            IUIDQuery, UIDQuery('uid_query'))
    except ValueError: # Already registered
        pass

    print >> out, "Successfully installed utilities of %s." % PKG_NAME
