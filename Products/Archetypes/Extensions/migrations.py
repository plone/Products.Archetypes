from Globals import PersistentMapping
from StringIO import StringIO
from Acquisition import aq_base
from Products.Archetypes.Extensions.utils import install_catalog
from Products.Archetypes.Extensions.utils import install_referenceCatalog
from Products.Archetypes.utils import make_uuid
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
            sourceObj.reindexObject() #try for a UID update


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

    else:
        # We had a reference catalog, make sure its doing annotation
        # based references
        rc = getattr(portal, REFERENCE_CATALOG)
        uc = getattr(portal, UID_CATALOG)

        # looks like its a folder with stuff in it.. old style
        # we want to do this quickly so we will grab all the
        # objects for each unique source ID and push them into
        # that source object
        sids = rc.uniqueValuesFor('sourceUID')
        for sid in sids:
            set = rc(sourceUID=sid)
            sourceObject = uc(UID=sid)[0].getObject()
            if not sourceObject: continue
            annotations = sourceObject._getReferenceAnnotations()
            for brain in set:
                # we need to uncatalog the ref at its current path
                # and then stick it on the new object and index it
                # again under its new relative pseudo path
                path = brain.getPath()
                ref = getattr(rc, path, None)
                if ref is None: continue
                if path.find('ref_') != -1:
                    rc.uncatalog_object(path)
                    uc.uncatalog_object(path)

                    # make sure id==uid
                    setattr(ref, UUID_ATTR, make_uuid())
                    ref.id = ref.UID()
                    # now stick this in the annotation
                    # unwrap the ref
                    ref = aq_base(ref)
                    annotations[ref.UID()] = ref
                rc._delOb(path)
            # I might have to do this each time (to deal with an
            # edge case), but I suspect not
            sourceObject._catalogRefs(portal)


    print >>out, "Migrated References"

def migrate(self):
    """migrate an AT site"""
    out = StringIO()
    portal = self

    print >>out, "Begin Migration"

    fixArchetypesTool(portal, out)
    toReferenceCatalog(portal, out)

    print >>out, "Archetypes Migration Successful"
    return out.getvalue()
