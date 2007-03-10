import os
from os.path import isdir, join
from types import *
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility

from Globals import package_home
from Globals import PersistentMapping
from OFS.ObjectManager import BadRequestException
from Acquisition import aq_base, aq_parent
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.DirectoryView import addDirectoryViews, \
     registerDirectory, manage_listAvailableDirectories
from Products.CMFCore.utils import getToolByName
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
from Products.Archetypes.ArchetypeTool import fixActionsForType
from Products.Archetypes.ArchetypeTool import listTypes
from Products.Archetypes.ArchetypeTool import process_types
from Products.Archetypes.ArchetypeTool import base_factory_type_information
from Products.Archetypes import types_globals
from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IReferenceCatalog
from Products.Archetypes.interfaces import IUIDCatalog
from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.interfaces.ITemplateMixin import ITemplateMixin
from Products.Archetypes.config import *

from Products.CMFFormController.Extensions.Install \
     import install as install_formcontroller

from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ISkinsTool
from Products.CMFCore.interfaces import ITypesTool

from Products.Archetypes.ReferenceEngine import manage_addReferenceCatalog
from Products.Archetypes.UIDCatalog import manage_addUIDCatalog


class Extra:
    """indexes extra properties holder"""

def install_dependencies(self, out, required=1):
    qi=queryUtility(IQuickInstallerTool)
    if qi is None:
        if required:
            raise RuntimeError, (
                'portal_quickinstaller tool could not be found, and it is '
                'required to install Archetypes dependencies')
        else:
            print >>out, install_formcontroller(self)

    if not qi.isProductInstalled('CMFFormController'):
        qi.installProduct('CMFFormController',locked=1)
        print >>out, 'Installing CMFFormController'
    if not qi.isProductInstalled('MimetypesRegistry'):
        qi.installProduct('MimetypesRegistry')
        print >>out, 'Installing MimetypesRegistry'
    if not qi.isProductInstalled('PortalTransforms'):
        qi.installProduct('PortalTransforms')
        print >>out, 'Installing PortalTransforms'

def install_archetypetool(self, out):
    at = queryUtility(IArchetypeTool)
    parent = getUtility(ISiteRoot)

    if at is None:
        addTool = self.manage_addProduct['Archetypes'].manage_addTool
        addTool('Archetype Tool')
        sm = getSiteManager()
        sm.registerUtility(aq_base(parent.archetype_tool), IArchetypeTool)
        print >>out, 'Installing Archetype Tool'
    else:
        # Migration from 1.0
        if not hasattr(aq_base(at), '_registeredTemplates'):
            at._registeredTemplates = PersistentMapping()
        if not hasattr(aq_base(at), 'catalog_map'):
            at.catalog_map = PersistentMapping()

def install_tools(self, out):
    # Backwards compat. People (eg: me!) may depend on that
    install_archetypetool(self, out)
    install_uidcatalog(self, out)

def install_uidcatalog(self, out, rebuild=False):
    index_defs=( ('UID', 'FieldIndex'),
                 ('Type', 'FieldIndex'),
                 ('id', 'FieldIndex'),
                 ('Title', 'FieldIndex'), # used for sorting
                 ('portal_type', 'FieldIndex'),
               )
    metadata_defs = ('UID', 'Type', 'id', 'Title', 'portal_type', 'meta_type')
    reindex = False
    catalog = queryUtility(IUIDCatalog)
    parent = getUtility(ISiteRoot)

    if catalog is not None and not IUIDCatalog.isImplementedBy(catalog):
        # got a catalog but it's doesn't implement IUIDCatalog
        parent.manage_delObjects([UID_CATALOG,])
        catalog = None
        rebuild = True

    if catalog is None:
        #Add a zcatalog for uids
        addCatalog = manage_addUIDCatalog
        addCatalog(self, UID_CATALOG, 'Archetypes UID Catalog')
        catalog = parent.uid_catalog
        sm = getSiteManager()
        sm.registerUtility(aq_base(catalog), IUIDCatalog)
        print >>out, 'Installing uid catalog'

    for indexName, indexType in index_defs:
        try: #ugly try catch XXX FIXME
            if indexName not in catalog.indexes():
                catalog.addIndex(indexName, indexType, extra=None)
                reindex = True
        except:
            pass

    for metadata in metadata_defs:
        if not indexName in catalog.schema():
            catalog.addColumn(metadata)
            reindex = True
    if reindex:
        catalog.manage_reindexIndex()
    elif rebuild:
        catalog.manage_rebuildCatalog()

def install_referenceCatalog(self, out, rebuild=False):
    catalog = queryUtility(IReferenceCatalog)
    parent = getUtility(ISiteRoot)

    if catalog is not None and not IReferenceCatalog.isImplementedBy(catalog):
        # got a catalog but it's doesn't implement IUIDCatalog
        parent.manage_delObjects([REFERENCE_CATALOG,])
        catalog = None
        rebuild = 1

    if not catalog:
        #Add a zcatalog for uids
        addCatalog = manage_addReferenceCatalog
        addCatalog(self, REFERENCE_CATALOG, 'Archetypes Reference Catalog')
        catalog = parent.reference_catalog
        sm = getSiteManager()
        sm.registerUtility(aq_base(catalog), IReferenceCatalog)
        print >>out, 'Installing reference catalog'
        schema = catalog.schema()
        for indexName, indexType in (
                                      ('UID', 'FieldIndex'),
                                      ('sourceUID', 'FieldIndex'),
                                      ('targetUID', 'FieldIndex'),
                                      ('relationship', 'FieldIndex'),
                                      ('targetId', 'FieldIndex'),
                                      ):
            try:
                catalog.addIndex(indexName, indexType, extra=None)
            except:
                pass
            try:
                if not indexName in schema:
                    catalog.addColumn(indexName)
            except:
                pass

        catalog.manage_reindexIndex()

    if rebuild:
        catalog = getUtility(IReferenceCatalog)
        catalog.manage_rebuildCatalog()

def install_templates(self, out):
    at = getUtility(IArchetypeTool)
    at.registerTemplate('base_view', 'Base View')
    
    # fix name of base_view
    #rt = at._registeredTemplates
    #if 'base_view' not in rt.keys() or rt['base_view'] == 'base_view':
    #    at.registerTemplate(base_view)

def install_additional_templates(self, out, types):
    """Registers additionals templates for TemplateMixin classes.
    """
    at = getUtility(IArchetypeTool)
    
    for t in types:
        klass = t['klass']
        if ITemplateMixin.isImplementedByInstancesOf(klass):
            portal_type = klass.portal_type
            default_view = getattr(klass, 'default_view', 'base_view')
            suppl_views = getattr(klass, 'suppl_views', ())
            views = []

            if not default_view:
                default_view = 'base_view'

            at.registerTemplate(default_view)
            views.append(default_view)

            for view in suppl_views:
                at.registerTemplate(view)
                views.append(view)

            at.bindTemplate(portal_type, views)

def install_subskin(self, out, globals=types_globals, product_skins_dir='skins'):
    skinstool=getUtility(ISkinsTool)

    product = globals['__name__']
    registry_key = "%s:%s" % (product, product_skins_dir)
    registered_directories = manage_listAvailableDirectories()
    if registry_key not in registered_directories:
        try:
            registerDirectory(registry_key, globals)
        except OSError, ex:
            if ex.errno == 2: # No such file or directory
                return
            raise
    try:
        addDirectoryViews(skinstool, product_skins_dir, globals)
    except BadRequestException, e:
        # TODO: find a better way to do this, but that seems not feasible
        #      until Zope stops using string exceptions
        if str(e).endswith(' is reserved.'):
            # trying to use a reserved identifier, let the user know
            #
            # remember the cmf reserve ids of objects in the root of the
            # portal !
            raise
        # directory view has already been added
        pass

    fullProductSkinsPath = os.path.join(package_home(globals), product_skins_dir)
    files = os.listdir(fullProductSkinsPath)
    for productSkinName in files:
        # skip directories with a dot or special dirs
        # or maybe just startswith('.')?
        if '.' in productSkinName or productSkinName in ('CVS', '_svn', '{arch}'):
            continue
        if isdir(join(fullProductSkinsPath, productSkinName)):
            for skinName in skinstool.getSkinSelections():
                path = skinstool.getSkinPath(skinName)
                path = [i.strip() for i in  path.split(',')]
                try:
                    if productSkinName not in path:
                        path.insert(path.index('custom') +1, productSkinName)
                except ValueError:
                    if productSkinName not in path:
                        path.append(productSkinName)
                path = ','.join(path)
                skinstool.addSkinSelection(skinName, path)

def install_types(self, out, types, package_name):
    typesTool = getUtility(ITypesTool)
    folderish = []
    for klass in types:
        try:
            typesTool._delObject(klass.portal_type)
        except:
            pass

        typeinfo_name = "%s: %s (%s)" % (package_name, klass.__name__,
                                         klass.meta_type)

        # get the meta type of the FTI from the class, use the
        # default FTI as default
        fti_meta_type = getattr(klass, '_at_fti_meta_type', None)
        if not fti_meta_type or fti_meta_type == 'simple item':
            ## rr: explicitly catching 'simple item' because
            ## CMF 2.0 removed the meta_type from the basic TIs :-(
            ## seems to me, 'manage_addTypeInformation' is just broken
            fti_meta_type = 'Factory-based Type Information'
        try:
            typesTool.manage_addTypeInformation(fti_meta_type,
                                                id=klass.portal_type,
                                                typeinfo_name=typeinfo_name)
        except ValueError:
            print "failed to add '%s'" %  klass.portal_type
            print "fti_meta_type = %s" % fti_meta_type
        ## rr: from CMF-2.0 onward typeinfo_name from the call above
        ## is ignored and we have to do some more work
        t, fti = _getFtiAndDataFor(typesTool, klass.portal_type, package_name)
        if t and fti:
            t.manage_changeProperties(**fti)
            if fti.has_key('aliases'):
                t.setMethodAliases(fti['aliases'])
        
        # Set the human readable title explicitly
        ## t = getattr(typesTool, klass.portal_type, None)
        if t:
            t.title = klass.archetype_name

        # If the class appears folderish and the 'use_folder_tabs' is
        # not set to a false value, then we add the portal_type to
        # Plone's 'use_folder_tabs' property
        use_folder_tabs = klass.isPrincipiaFolderish and \
                          getattr(klass, 'use_folder_tabs', 1)
        if use_folder_tabs:
            folderish.append(klass.portal_type)
    if folderish:
        pt = queryUtility(IPropertiesTool)
        if pt is None:
            return
        sp = getattr(pt, 'site_properties', None)
        if sp is None:
            return
        props = ('use_folder_tabs', 'typesLinkToFolderContentsInFC')
        for prop in props:
            folders = sp.getProperty(prop, None)
            if folders is None:
                continue
            folders = list(folders)
            folders.extend(folderish)
            folders = tuple(dict(zip(folders, folders)).keys())
            sp._updateProperty(prop, folders)

def _getFtiAndDataFor(tool, typename, package_name):
    """helper method for type info setting
       returns fti object from the types tool and the data created
       by process_types for the fti
    """
    t = getattr(tool, typename, None)
    if t is None:
        return None, None
    all_ftis = process_types(listTypes(package_name),
                             package_name)[2]
    for fti in all_ftis:
        if fti['id'] == typename:
            fti['content_meta_type'] = fti['meta_type']
            return t, fti
    return t, None
    

def install_actions(self, out, types):
    typesTool = getUtility(ITypesTool)
    for portal_type in types:
        ## rr: XXX TODO somehow the following doesn't do anymore what
        ## it used to do :-(
        fixActionsForType(portal_type, typesTool)

def install_indexes(self, out, types):
    portal_catalog = catalog = getUtility(ICatalogTool)
    for cls in types:
        if 'indexes' not in cls.installMode:
            continue

        for field in cls.schema.fields():
            if not field.index:
                continue

            if type(field.index) is StringType:
                index = (field.index,)
            elif isinstance(field.index, (TupleType, ListType) ):
                index = field.index
            else:
                raise SyntaxError("Invalid Index Specification %r"
                                  % field.index)

            for alternative in index:
                installed = None
                index_spec = alternative.split(':', 1)
                use_column  = 0
                if len(index_spec) == 2 and index_spec[1] in ('schema', 'brains'):
                    use_column = 1
                index_spec = index_spec[0]

                accessor = field.getIndexAccessorName()

                parts = index_spec.split('|')
                # we want to be able to specify which catalog we want to use
                # for each index. syntax is
                # index=('member_catalog/:schema',)
                # portal catalog is used by default if not specified
                if parts[0].find('/') > 0:
                    str_idx = parts[0].find('/')
                    catalog_name = parts[0][:str_idx]
                    parts[0] = parts[0][str_idx+1:]
                    catalog = getToolByName(self, catalog_name)
                else:
                    catalog = portal_catalog
                
                #####################
                # add metadata column 
                
                # lets see if the catalog is itself an Archetype:
                isArchetype = IBaseObject.isImplementedBy(catalog)
                # archetypes based zcatalogs need to provide a different method 
                # to list its schema-columns to not conflict with archetypes 
                # schema                
                hasNewWayMethod = hasattr(catalog, 'zcschema')
                hasOldWayMethod = not isArchetype and hasattr(catalog, 'schema')
                notInNewWayResults = hasNewWayMethod and accessor not in catalog.zcschema()
                notInOldWayResults = hasOldWayMethod and accessor not in catalog.schema()
                if use_column and (notInNewWayResults or notInOldWayResults):
                    try:
                        catalog.addColumn(accessor)
                    except:
                        import traceback
                        traceback.print_exc(file=out)

                ###########
                # add index
                
                # if you want to add a schema field without an index
                #if not parts[0]:
                #    continue

                for itype in parts:
                    extras = itype.split(',')
                    if len(extras) > 1:
                        itype = extras[0]
                        props = Extra()
                        for extra in extras[1:]:
                            name, value = extra.split('=')
                            setattr(props, name.strip(), value.strip())
                    else:
                        props = None
                    try:
                        #Check for the index and add it if missing
                        catalog.addIndex(accessor, itype,
                                         extra=props)
                        catalog.manage_reindexIndex(ids=(accessor,))
                    except:
                        # FIXME: should only catch "Index Exists"
                        # damned string exception !
                        pass
                    else:
                        installed = 1
                        break

                if installed:
                    break


def isPloneSite(self):
    # we should just define a single attr for this
    if self.__class__.__name__ == "PloneSite":
        return 1
    for base in self.__class__.__bases__:
        if base.__name__ == "PloneSite":
            return 1
    if 'plone_utils' in self.objectIds():
        # Possibly older PloneSite
        # It may be risky to assert this, but the user should
        # have upgrade anyway, so its his fault :)
        return 1
    return 0


def filterTypes(self, out, types, package_name):
    typesTool = getUtility(ITypesTool)

    filtered_types = []

    for rti in types:
        t = rti['klass']
        name = rti['name']
        meta_type = rti['meta_type']

        ## rr: skipping the first check as 'listDefaultTypeInformation
        ## isn't available anymore in CMF-2.0. For now we rely on the
        ## types being passed in to be safe

##         # CMF 1.4 name: (product_id, metatype)
##         typeinfo_name="%s: %s" % (package_name, meta_type)
##         # CMF 1.5 name: (product_id, id, metatype)
##         typeinfo_name2="%s: %s (%s)" % (package_name, name, meta_type)
##         info = typesTool.listDefaultTypeInformation()
##         found = 0
##         for (name, ft) in info:
##             #if name.startswith(typeinfo_name):
##             if name in (typeinfo_name, typeinfo_name2):
##                 found = 1
##                 break

##         if not found:
##             print >> out, ('%s is not a registered Type '
##                            'Information' % typeinfo_name)
##             continue

        isBaseObject = 0
        if IBaseObject.isImplementedByInstancesOf(t):
            isBaseObject = 1
        else:
            for k in t.__bases__:
                if IBaseObject.isImplementedByInstancesOf(k):
                    isBaseObject = 1
                    break

        if isBaseObject:
            filtered_types.append(t)
        else:
            print >> out, ("%s doesnt implements IBaseObject. "
                           "Possible misconfiguration. "
                           "Check if your class has an "
                           "'__implements__ = IBaseObject' "
                           "(or IBaseContent, or IBaseFolder)" % repr(t))

    return filtered_types

def setupArchetypes(self, out, require_dependencies=True):
    # installing dependency products
    install_dependencies(self, out, require_dependencies)

    # install archetype tools and templates
    install_archetypetool(self, out)
    install_uidcatalog(self, out, rebuild=False)
    install_referenceCatalog(self, out, rebuild=False)

    # install skins and register templates
    install_subskin(self, out, types_globals)
    install_templates(self, out)

def setupEnvironment(self, out, types,
                     package_name,
                     globals=types_globals,
                     product_skins_dir='skins',
                     require_dependencies=True,
                     install_deps=1):

    if install_deps:
        qi = queryUtility(IQuickInstallerTool)
        if qi is None:
            setupArchetypes(self, out, require_dependencies=require_dependencies)
        else:
            if not qi.isProductInstalled('Archetypes'):
                qi.installProduct('Archetypes')
                print >>out, 'Installing Archetypes'

    if product_skins_dir:
        install_subskin(self, out, globals, product_skins_dir)

    install_additional_templates(self, out, types)

    ftypes = filterTypes(self, out, types, package_name)
    install_indexes(self, out, ftypes)
    install_actions(self, out, ftypes)

def doubleCheckDefaultTypeActions(self, ftypes):
    # rr: for some reason, AT's magic wrt adding the default type actions
    # stopped working when moving to CMF-2.0
    # Instead of trying to resurect the old way (which I tried but couldn't)
    # I make it brute force here

    typesTool = getUtility(ITypesTool)
    defaultTypeActions = [ActionInformation(**action) for action in
                          base_factory_type_information[0]['actions']]

    for ftype in ftypes:
        portal_type = ftype.portal_type
        fti = typesTool.get(portal_type, None)
        if fti is None:
            continue
        actions = list(fti._actions)
        action_ids = [a.id for a in actions]
        prepend = []
        for a in defaultTypeActions:
            if a.id not in action_ids:
                prepend.append(a.clone())
        if prepend:
            fti._actions = tuple(prepend + actions)
    

## The master installer
def installTypes(self, out, types, package_name,
                 globals=types_globals, product_skins_dir='skins',
                 require_dependencies=True, refresh_references=False,
                 install_deps=True):
    """Use this for your site with your types"""
    ftypes = filterTypes(self, out, types, package_name)
    install_types(self, out, ftypes, package_name)
    # Pass the unfiltered types into setup as it does that on its own
    setupEnvironment(self, out, types, package_name,
                     globals, product_skins_dir, require_dependencies,
                     install_deps)
    ## rr: sometimes the default actions are still missing
    doubleCheckDefaultTypeActions(self, ftypes)
    if refresh_references and ftypes:
        rc = getUtility(IReferenceCatalog)
        rc.manage_rebuildCatalog()

def refreshReferenceCatalog(self, out, types=None, package_name=None, ftypes=None):
    """refresh the reference catalog to reindex objects after reinstalling a
    AT based product.
    
    This may take a very long time but it seems to be required under some
    circumstances.
    """
    assert package_name

    if ftypes is None:
        ftypes = filterTypes(self, out, types, package_name)

    if not ftypes and not types:
        # no types to install
        return

    rc = getUtility(IReferenceCatalog)
    mt = tuple([t.meta_type for t in ftypes])
    
    # because manage_catalogFoundItems sucks we have to do it on our own ...
    func    = rc.catalog_object
    obj     = self
    path    = '/'.join(obj.getPhysicalPath())
    REQUEST = self.REQUEST

    rc.ZopeFindAndApply(obj,
                        obj_metatypes=mt,
                        search_sub=1,
                        REQUEST=REQUEST,
                        apply_func=func,
                        apply_path=path)
