from ZODB.PersistentMapping import PersistentMapping
from StringIO import StringIO
from Products.Archetypes.Extensions.utils import install_catalog

def fixArchetypesTool(portal, out):
    at = portal.archetype_tool

    if not hasattr(at, '_templates'):
        #They come in pairs
        at._templates = PersistentMapping()
        at._registeredTemplates = PersistentMapping()

    if not hasattr(at, 'catalog_map'):
        at.catalog_map = PersistentMapping()

    install_catalog(portal, out)
    


def migrate(self):
    out = StringIO()
    portal = self
    
    fixArchetypesTool(portal, out)

    print >>out, "Archetypes Migration Successful"
    return out.getvalue()
