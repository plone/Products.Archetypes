from Globals import PersistentMapping
from StringIO import StringIO
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Extensions.utils import install_uidcatalog
from Products.Archetypes.utils import make_uuid
from Products.Archetypes.config import *
from Products.Archetypes.interfaces.base import IBaseObject

# WARNING!
# Using full transactions after every migration step may be dangerous but it's
# required if you don't have enough space and memory
USE_FULL_TRANSACTIONS = False

def reinstallArchetypes(portal,out):
    ''' lets quickinstaller reinstall the archetypes '''
    # heuristic: if there is no reference_catalog, lets reinstall
    refcat=getToolByName(portal,REFERENCE_CATALOG,None)
    if not refcat:
        print >>out, 'reinstalling Archetypes...'
        getToolByName(portal,'portal_quickinstaller').reinstallProducts(['Archetypes'])
        print >>out, 'reinstalled Archetypes.'
        
def fixArchetypesTool(portal, out):
    at = portal.archetype_tool

    if not hasattr(at, '_templates'):
        #They come in pairs
        at._templates = PersistentMapping()
        at._registeredTemplates = PersistentMapping()

    if not hasattr(at, 'catalog_map'):
        at.catalog_map = PersistentMapping()

    install_uidcatalog(portal, out)


def migrateReferences(portal, out):
    # FIRST
    # a 1.2 -> 1.3 (new annotation style) migration path
    
    at = getToolByName(portal, TOOL_NAME)
    rc = getToolByName(portal, REFERENCE_CATALOG)
    uc = getToolByName(portal, UID_CATALOG)

    count=0
    
    # Old 1.2 style references are stored inside archetype_tool on the 'ref'
    # attribute
    refs = getattr(at, 'refs', None)
    if refs is not None:
        print >>out, 'migrating reference from Archetypes 1.2'
        count=0
        print >>out, "Old references are stored in %s, so migrating them to new style reference annotations." % (TOOL_NAME)
        allbrains = uc()
        for brain in allbrains:
            sourceObj = brain.getObject()
            sourceUID = getattr(aq_base(sourceObj), olduididx, None)
            if sourceUID is None: continue
            # references migration starts
            for targetUID, relationship in refs.get(sourceUID, []):
                # get target object
                targetBrains = uc(**{olduididx:targetUID})
                assert(len(targetBrains) == 1,'catalog query for OLD uid (%s) returned %d results instead of 1' % (targetUID,len(targetBrains)))
                targetObj=targetBrains[0].getObject()
                # create new style reference
                rc.addReference(sourceObj, targetObj, relationship)
                count+=1        
                # avoid eating up all RAM
                if not count % 250:
                    get_transaction().commit(1) 
                print >>out, "%s old references migrated." % count
        # after all remove the old-style reference attribute
        delattr(at, 'refs')
        if USE_FULL_TRANSACTIONS:
            get_transaction().commit()
        else:
            get_transaction().commit(1)
    
    else:
        # SECOND
        # a 1.3.b2 -> 1.3 (new annotation style) migration path
        # We had a reference catalog, make sure its doing annotation
        # based references
    
        # reference metadata cannot be restored since reference-catalog is no more
        # a btree and in AT 1.3.b2 reference_catalog was a btreefolder

        print >>out, 'migrating reference from Archetypes 1.3. beta2'

        refs = rc()
        rc.manage_catalogClear()
        for brain in refs:
            sourceObject = rc.lookupObject(brain.sourceUID)
            if sourceObject is None: continue
            targetObject=rc.lookupObject(brain.targetUID)
            if not targetObject:
                print >>out,  'mirateReferences: Warning: no targetObject found for UID ',brain.targetUID
                continue
                
            count+=1
            sourceObject.addReference(targetObject,relationship=brain.relationship)
            # avoid eating up all RAM
            if not count % 250:
                get_transaction().commit(1) 

        print >>out, "%s old references migrated (reference metadata not restored)." % count

        if USE_FULL_TRANSACTIONS:
            get_transaction().commit()
        else:
            get_transaction().commit(1)

    print >>out, "Migrated References"


    #Reindex for new UUIDs
    uc.manage_reindexIndex()
    rc.manage_reindexIndex()

olduididx = 'old_tmp_at_uid'

def migrateUIDs(portal, out):
    count=0
    uc = getToolByName(portal, UID_CATALOG)    
    
    # temporary add a new index    
    if olduididx not in uc.indexes():
        uc.addIndex(olduididx, 'FieldIndex', extra=None)
        if not olduididx in uc.schema():
            uc.addColumn(olduididx)
    
    # clear UID Catalog 
    uc.manage_catalogClear()
    
    # rebuild UIDS on objects and in catalog
    allbrains = portal.portal_catalog()
    for brain in allbrains:
        # get a uid for each thingie
        obj = brain.getObject()
        if not IBaseObject.isImplementedBy(obj): 
            continue #its no Archetype instance, so leave it
        
        objUID = getattr(aq_base(obj), '_uid', None)        
        if objUID is not None: #continue    # not an old style AT?
            setattr(obj, olduididx, objUID) # this one can be part of the catalog
            delattr(obj, '_uid')
            setattr(obj, UUID_ATTR, None)
        obj._register()            # creates a new UID
        obj._updateCatalog(portal) # to be sure
        count+=1
        # avoid eating up all RAM
        if not count % 250:
            get_transaction().commit(1) 

    if USE_FULL_TRANSACTIONS:
        get_transaction().commit()
    else:
        get_transaction().commit(1)

    print >>out, count, "UID's migrated."

def removeOldUIDs(portal, out):
    # remove temporary needed index 
    uc = getToolByName(portal, UID_CATALOG)    
    if olduididx in uc.indexes():
        uc.delIndex(olduididx)
        if olduididx in uc.schema():
            uc.delColumn(olduididx)
    count=0
    allbrains = uc()
    for brain in allbrains:
        #Get a uid for each thingie
        obj = brain.getObject()
        objUID = getattr(aq_base(obj), olduididx, None)        
        if objUID is None: continue # not an old style AT
        delattr(obj, olduididx)
        obj._updateCatalog(portal) 
        count+=1
        # avoid eating up all RAM
        if not count % 250:
            get_transaction().commit(1) 

    if USE_FULL_TRANSACTIONS:
        get_transaction().commit()
    else:
        get_transaction().commit(1)

    print >>out, count, "old UID attributes removed."

def migrateSchemas(portal, out):
    at = getToolByName(portal, TOOL_NAME)
    msg = at.manage_updateSchema(update_all=1)
    if USE_FULL_TRANSACTIONS:
        get_transaction().commit()
    else:
        get_transaction().commit(1)
    print >>out, msg

def migrateCatalogIndexes(portal, out):
    def addIndex(catalog, indexName, indexType):
        # copy of code in utils.py:install_referenceCatalog
        try:
            catalog.addIndex(indexName, indexType, extra=None)
        except:
            pass
        try:
            if not indexName in catalog.schema():
                catalog.addColumn(indexName)
        except:
            pass
    
    rc = getToolByName(portal, REFERENCE_CATALOG)
    add_indexes = ('targetId', 'FieldIndex'),
    [addIndex(rc, n, t) for n, t in add_indexes]
    
def refreshCatalogs(portal, out):
    uc = getToolByName(portal, UID_CATALOG)
    rc = getToolByName(portal, REFERENCE_CATALOG)
    print >>out, 'Refreshing uid catalog'
    uc.refreshCatalog(clear=1)
    print >>out, 'Refreshing reference catalog'
    rc.refreshCatalog(clear=1)

    if USE_FULL_TRANSACTIONS:
        get_transaction().commit()
    else:
        get_transaction().commit(1)


def migrate(self):
    """migrate an AT site"""
    out = StringIO()
    portal = self

    print >>out, "Begin Migration"

    fixArchetypesTool(portal, out)
    reinstallArchetypes(portal,out)
    migrateSchemas(portal, out)
    migrateUIDs(portal, out)
    migrateReferences(portal,out)
    removeOldUIDs(portal, out)
    migrateCatalogIndexes(portal, out)
    refreshCatalogs(portal, out)
    print >>out, "Archetypes Migration Successful"
    return out.getvalue()
