import traceback, os
from os.path import isdir, join
from types import *

from Globals import package_home
from Globals import PersistentMapping
from OFS.ObjectManager import BadRequestException
from Acquisition import aq_base, aq_parent
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.DirectoryView import addDirectoryViews, \
     registerDirectory, manage_listAvailableDirectories
from Products.CMFCore.utils import getToolByName, minimalpath
from Products.Archetypes.ArchetypeTool import fixActionsForType
from Products.Archetypes import types_globals
from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.config import *

from Products.PortalTransforms.Extensions.Install \
     import install as install_portal_transforms
from Products.MimetypesRegistry.Extensions.Install \
     import install as install_mimetypes_registry

from Products.Archetypes.ReferenceEngine import \
     manage_addReferenceCatalog, manage_addUIDCatalog
from Products.Archetypes.interfaces.referenceengine import \
     IReferenceCatalog, IUIDCatalog

class Extra:
    """indexes extra properties holder"""

def install_dependencies(self, out, required=1):
    qi=getToolByName(self, 'portal_quickinstaller', None)
    if qi is None:
        if required:
            raise RuntimeError, (
                'portal_quickinstaller tool could not be found, and it is '
                'required to install Archetypes dependencies')
        else:
            return
    qi.installProduct('CMFFormController',locked=1)
    qi.installProduct('MimetypesRegistry',)
    qi.installProduct('PortalTransforms',)

def install_tools(self, out):
    at = getToolByName(self, 'archetype_tool', None)
    if at is None:
        addTool = self.manage_addProduct['Archetypes'].manage_addTool
        addTool('Archetype Tool')

        at = getToolByName(self, 'archetype_tool', None)
        ##Test some of the templating code
        at.registerTemplate('base_view', "Normal View")
    else:
        # Migration from 1.0
        if not hasattr(aq_base(at), '_registeredTemplates'):
            at._registeredTemplates = PersistentMapping()
        if not hasattr(aq_base(at), 'catalog_map'):
            at.catalog_map = PersistentMapping()

    install_catalog(self, out)

def install_catalog(self, out, rebuild=0):

    index_defs=( ('UID', 'FieldIndex'),
                 ('Type', 'FieldIndex'),
                 ('id', 'FieldIndex'),
                 ('Title', 'FieldIndex'),
                 ('portal_type', 'FieldIndex'),
               )

    catalog = getToolByName(self, UID_CATALOG, None)
    if catalog and not IUIDCatalog.isImplementedBy(catalog):
        # got a catalog but it's doesn't implement IUIDCatalog
        aq_parent(catalog).manage_delObjects([UID_CATALOG,])
        catalog = None
        rebuild = 1

    if not catalog:
        #Add a zcatalog for uids
        addCatalog = manage_addUIDCatalog
        addCatalog(self, UID_CATALOG, 'Archetypes UID Catalog')
        catalog = getToolByName(self, UID_CATALOG)

    #catalog = getToolByName(self, UID_CATALOG)
    for indexName, indexType in index_defs:
        try: #ugly try catch XXX FIXME
            if indexName not in catalog.indexes():
                catalog.addIndex(indexName, indexType, extra=None)
            if not indexName in catalog.schema():
                catalog.addColumn(indexName)
        except:
            pass

    catalog.manage_reindexIndex()
    if rebuild:
        catalog.manage_rebuildCatalog()

def install_referenceCatalog(self, out, rebuild=0):
    catalog = getToolByName(self, REFERENCE_CATALOG, None)
    if catalog and not IReferenceCatalog.isImplementedBy(catalog):
        # got a catalog but it's doesn't implement IUIDCatalog
        aq_parent(catalog).manage_delObjects([REFERENCE_CATALOGG,])
        catalog = None
        rebuild = 1

    if not catalog:
        #Add a zcatalog for uids
        addCatalog = manage_addReferenceCatalog
        addCatalog(self, REFERENCE_CATALOG, 'Archetypes Reference Catalog')
        catalog = getToolByName(self, REFERENCE_CATALOG)
        schema = catalog.schema()
        for indexName, indexType in (
                                      ('UID', 'FieldIndex'),
                                      ('sourceUID', 'FieldIndex'),
                                      ('targetUID', 'FieldIndex'),
                                      ('relationship', 'FieldIndex'),
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
        catalog = getToolByName(self, REFERENCE_CATALOG)
        catalog.manage_rebuildCatalog()

def install_templates(self, out):
    at = self.archetype_tool
    at.registerTemplate('base_view')



def install_subskin(self, out, globals=types_globals, product_skins_dir='skins'):
    skinstool=getToolByName(self, 'portal_skins')

    fullProductSkinsPath = os.path.join(package_home(globals), product_skins_dir)
    productSkinsPath = minimalpath(fullProductSkinsPath)
    registered_directories = manage_listAvailableDirectories()
    if productSkinsPath not in registered_directories:
        try:
            registerDirectory(product_skins_dir, globals)
        except OSError, ex:
            if ex.errno == 2: # No such file or directory
                return
            raise
    try:
        addDirectoryViews(skinstool, product_skins_dir, globals)
    except BadRequestException, e:
        pass  # directory view has already been added

    files = os.listdir(fullProductSkinsPath)
    for productSkinName in files:
        if (isdir(join(fullProductSkinsPath, productSkinName))
            and productSkinName != 'CVS'
            and productSkinName != '.svn'):
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
    typesTool = getToolByName(self, 'portal_types')
    folderish = []
    for type in types:
        try:
            typesTool._delObject(type.portal_type)
        except:
            pass

        typeinfo_name = "%s: %s" % (package_name, type.meta_type)

        typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                                id=type.portal_type,
                                                typeinfo_name=typeinfo_name)
        # Set the human readable title explicitly
        t = getattr(typesTool, type.portal_type, None)
        if t:
            t.title = type.archetype_name

        # If the class appears folderish and the 'use_folder_tabs' is
        # not set to a false value, then we add the portal_type to
        # Plone's 'use_folder_tabs' property
        use_folder_tabs = type.isPrincipiaFolderish and getattr(type, 'use_folder_tabs', 1)
        if use_folder_tabs:
            folderish.append(type.portal_type)
    if folderish:
        pt = getToolByName(self, 'portal_properties', None)
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


def install_actions(self, out, types):
    typesTool = getToolByName(self, 'portal_types')
    for portal_type in types:
        fixActionsForType(portal_type, typesTool)

def install_indexes(self, out, types):

    for cls in types:
        if 'indexes' not in cls.installMode:
            continue

        for field in cls.schema.fields():
            if field.index:
                portal_catalog = catalog = getToolByName(self, 'portal_catalog')

                if type(field.index) is StringType:
                    index = (field.index,)
                elif isinstance(field.index, (TupleType, ListType) ):
                    index = field.index
                else:
                    raise SyntaxError("Invalid Index Specification %r"%field.index)

                for alternative in index:
                    installed = None
                    index_spec = alternative.split(':', 1)
                    use_column  = 0
                    if len(index_spec) == 2 and index_spec[1] in ('schema', 'brains'):
                        use_column = 1
                    index_spec = index_spec[0]

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

                    if use_column:
                        try:
                            if field.accessor not in catalog.schema():
                                catalog.addColumn(field.accessor)
                        except:
                            import traceback
                            traceback.print_exc(file=out)

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
                            catalog.addIndex(field.accessor, itype,
                                             extra=props)
                            catalog.manage_reindexIndex(ids=(field.accessor,))
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
    typesTool = getToolByName(self, 'portal_types')

    filtered_types = []

    for rti in types:
        t = rti['klass']

        typeinfo_name="%s: %s" % (package_name, t.meta_type)
        info = typesTool.listDefaultTypeInformation()
        found = 0
        for (name, ft) in info:
            if name == typeinfo_name:
                found = 1
                break

        if not found:
            print >> out, ('%s is not a registered Type '
                           'Information' % typeinfo_name)
            continue

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


def setupEnvironment(self, out, types,
                     package_name,
                     globals=types_globals,
                     product_skins_dir='skins',
                     require_dependencies=1):

    install_dependencies(self, out, require_dependencies)

    types = filterTypes(self, out, types, package_name)
    install_tools(self, out)
    install_referenceCatalog(self, out)

    if product_skins_dir:
        install_subskin(self, out, globals, product_skins_dir)



    install_templates(self, out)

    install_indexes(self, out, types)
    install_actions(self, out, types)

    install_portal_transforms(self)
    install_mimetypes_registry(self)


## The master installer
def installTypes(self, out, types, package_name,
                 globals=types_globals, product_skins_dir='skins',
                 require_dependencies=1,
                 refresh_references=1):
    """Use this for your site with your types"""
    ftypes = filterTypes(self, out, types, package_name)
    install_types(self, out, ftypes, package_name)
    # Pass the unfiltered types into setup as it does that on its own
    setupEnvironment(self, out, types, package_name,
                     globals, product_skins_dir, require_dependencies)
    if refresh_references and ftypes:
        refreshReferenceCatalog(self, out, package_name=package_name, 
                                ftypes=ftypes)

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

    rc = getToolByName(self, REFERENCE_CATALOG)
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
