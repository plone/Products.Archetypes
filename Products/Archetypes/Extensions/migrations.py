from ZODB.PersistentMapping import PersistentMapping
from StringIO import StringIO
from Products.Archetypes.Extensions.utils import install_catalog
from Products.Archetypes.Extensions.utils import install_referenceCatalog

from Products.Archetypes.config import *

def fixArchetypesTool(portal, out):
    at = portal.archetype_tool

    if not hasattr(at, '_templates'):
        #They come in pairs
        at._templates = PersistentMapping()
        at._registeredTemplates = PersistentMapping()

    if not hasattr(at, 'catalog_map'):
        at.catalog_map = PersistentMapping()

    install_catalog(portal, out)

def toReferenceCatalog(portal, out):
    if not hasattr(portal, REFERENCE_CATALOG):
        install_referenceCatalog(portal, out)
        print >>out, "Added Reference Catalog"
        
        rc = getattr(portal, REFERENCE_CATALOG)
        uc = getattr(portal, UID_CATALOG)
        
        #Now map the old references on AT to the RC
        at = portal.archetype_tool
        refs = getattr(at, 'refs', None)
        if not refs: return

        #we want to
        # assign new UUIDs
        # map old refs to new UUIDs in the new catalog
        # remove the old mappings from the AT

        # adding new reference using the RC will accomplish our goals
        # and then we can delete the old '_uid' attr
        allbrains = portal.portal_catalog()
        for brain in allbrains:
            #Get a uid for each thingie
            sourceObj = brain.getObject()
            sourceUID = getattr(sourceObj.aq_base, '_uid', None)
            if not sourceUID: continue
            rc.registerObject(sourceObj)

        uc.manage_reindexIndex()
            
        for brain in allbrains:
            sourceObj = brain.getObject()
            sourceUID = getattr(sourceObj.aq_base, '_uid', None)
            if not sourceUID: continue

            for targetUID, relationship in refs.get(sourceUID, []):
                tObj = uc(UID=targetUID)[0].getObject()
                rc.addReference(sourceObj, tObj, relationship)

        #remove all the old UIDs
        for brain in allbrains:
            sObject = brain.getObject()
            if hasattr(sObject, '_uid'):
                delattr(sObject, '_uid')

        #Reindex for new UUIDs
        uc.manage_reindexIndex()
        rc.manage_reindexIndex()
        print >>out, "Migrated References"
                
def migrate(self):
    """migrate an AT site"""
    out = StringIO()
    portal = self
    print >>out, "Being Migration"
    
    fixArchetypesTool(portal, out)
    toReferenceCatalog(portal, out)
    
    print >>out, "Archetypes Migration Successful"
    return out.getvalue()
