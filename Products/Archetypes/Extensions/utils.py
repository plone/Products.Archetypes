import sys, traceback, os
from os.path import isdir, join
from types import *

from Globals import package_home
from Globals import PersistentMapping
from OFS.ObjectManager import BadRequestException
from Acquisition import aq_base
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.DirectoryView import addDirectoryViews, \
     registerDirectory, createDirectoryView, manage_listAvailableDirectories
from Products.CMFCore.utils import getToolByName, minimalpath
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression
from Products.Archetypes.ArchetypeTool import fixActionsForType
from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.utils import findDict
from Products.Archetypes import types_globals
from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.config import *

from Products.PortalTransforms.Extensions.Install \
     import install as install_portal_transforms

from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.Archetypes.ReferenceEngine import manage_addReferenceCatalog

class Extra:
    """indexes extra properties holder"""

def install_dependencies(self, out):
    qi=getToolByName(self, 'portal_quickinstaller')
    qi.installProduct('CMFFormController',locked=1)
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

def install_catalog(self, out):

    index_defs=(('UID', 'FieldIndex'),
                 ('Type', 'FieldIndex'),
                 ('id', 'FieldIndex'),
                 ('Title', 'FieldIndex'),
                 ('portal_type', 'FieldIndex'),
             )

    if not hasattr(self, UID_CATALOG):
        #Add a zcatalog for uids
        addCatalog = manage_addZCatalog
        addCatalog(self, UID_CATALOG, 'Archetypes UID Catalog')

    catalog = getToolByName(self, UID_CATALOG)
    schema = catalog.schema()
    indexes = catalog.indexes()
    schemaFields = []

    for indexName, indexType in ( ('UID', 'FieldIndex'),
                                  ('Type', 'FieldIndex'),
                                  ('id', 'FieldIndex'),
                                  ('Title', 'FieldIndex'),
                                  ('portal_type', 'FieldIndex'),
                                  ):
        try:
            if indexName not in indexes:
                catalog.addIndex(indexName, indexType, extra=None)
            if not indexName in schema:
                catalog.addColumn(indexName)
                schemaFields.append(indexName)
        except:
            pass

    catalog.manage_reindexIndex(ids=schemaFields)

def install_templates(self, out):
    at = self.archetype_tool
    at.registerTemplate('base_view')


def install_referenceCatalog(self, out):
    if not hasattr(self, REFERENCE_CATALOG):
        #Add a zcatalog for uids
        addCatalog = manage_addReferenceCatalog
        addCatalog(self, REFERENCE_CATALOG, 'Archetypes Reference Catalog')
        catalog = getToolByName(self, REFERENCE_CATALOG)
        schema = catalog.schema()
        for indexName, indexType in ( ('sourceUID', 'FieldIndex'),
                                      ('targetUID', 'FieldIndex'),
                                      ('relationship', 'FieldIndex'),
                                      ('targetId', 'FieldIndex'),
                                      ('targetTitle', 'FieldIndex'),
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

        #catalog.manage_reindexIndex()


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
    for type in types:
        try:
            typesTool._delObject(type.portal_type)
        except:
            pass

        typeinfo_name = "%s: %s" % (package_name, type.meta_type)

        typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                                id=type.portal_type,
                                                typeinfo_name=typeinfo_name)
        # set the human readable title explicitly
        t = getattr(typesTool, type.portal_type, None)
        if t:
            t.title = type.archetype_name

def install_actions(self, out, types):
    typesTool = getToolByName(self, 'portal_types')
    for portal_type in types:
        fixActionsForType(portal_type, typesTool)

def install_indexes(self, out, types):
    catalog = getToolByName(self, 'portal_catalog')
    catalog = aq_base(catalog)

    for cls in types:
        if 'indexes' not in cls.installMode:
            continue

        for field in cls.schema.fields():
            if field.index:
                if type(field.index) is StringType:
                    index = (field.index,)
                else:
                    index = field.index

                for alternative in index:
                    installed = None
                    schema = alternative.split(':', 1)
                    if len(schema) == 2 and schema[1] == 'schema':
                        # FIXME: why do we try/except this part ?
                        try:
                            if field.accessor not in catalog.schema():
                                catalog.addColumn(field.accessor)
                        except:
                            import traceback
                            traceback.print_exc(file=out)

                    # we may want to add a field to metadata without
                    # indexing it
                    if not schema[0]:
                        continue

                    parts = schema[0].split('|')

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
                     product_skins_dir='skins'):

    install_dependencies(self, out)

    types = filterTypes(self, out, types, package_name)
    install_tools(self, out)
    install_referenceCatalog(self, out)

    if product_skins_dir:
        install_subskin(self, out, globals, product_skins_dir)



    install_templates(self, out)

    install_indexes(self, out, types)
    install_actions(self, out, types)

    install_portal_transforms(self)


## The master installer
def installTypes(self, out, types, package_name,
                 globals=types_globals, product_skins_dir='skins'):
    """Use this for your site with your types"""
    ftypes = filterTypes(self, out, types, package_name)
    install_types(self, out, ftypes, package_name)
    # Pass the unfiltered types into setup as it does that on its own
    setupEnvironment(self, out, types, package_name,
                     globals, product_skins_dir)
