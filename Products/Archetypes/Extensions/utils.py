import os
from os.path import isdir, join

from App.Common import package_home
from OFS.ObjectManager import BadRequestException
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.DirectoryView import addDirectoryViews, \
    registerDirectory, manage_listAvailableDirectories
from Products.CMFCore.utils import getToolByName, getPackageName
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.ArchetypeTool import fixActionsForType
from Products.Archetypes.ArchetypeTool import listTypes
from Products.Archetypes.ArchetypeTool import process_types
from Products.Archetypes.ArchetypeTool import base_factory_type_information
from Products.Archetypes import types_globals
from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.interfaces.ITemplateMixin import ITemplateMixin


class Extra:
    """indexes extra properties holder"""


def install_additional_templates(self, out, types):
    """Registers additionals templates for TemplateMixin classes.
    """
    at = getToolByName(self, 'archetype_tool')

    for t in types:
        klass = t['klass']
        if ITemplateMixin.implementedBy(klass):
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
    skinstool = getToolByName(self, 'portal_skins')

    product = getPackageName(globals)
    registry_key = "%s:%s" % (product, product_skins_dir)
    registered_directories = manage_listAvailableDirectories()
    if registry_key not in registered_directories:
        try:
            registerDirectory(product_skins_dir, globals)
        except OSError, ex:
            if ex.errno == 2:  # No such file or directory
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

    fullProductSkinsPath = os.path.join(
        package_home(globals), product_skins_dir)
    files = os.listdir(fullProductSkinsPath)
    for productSkinName in files:
        # skip directories with a dot or special dirs
        # or maybe just startswith('.')?
        if '.' in productSkinName or productSkinName in ('CVS', '_svn', '{arch}'):
            continue
        if isdir(join(fullProductSkinsPath, productSkinName)):
            for skinName in skinstool.getSkinSelections():
                path = skinstool.getSkinPath(skinName)
                path = [i.strip() for i in path.split(',')]
                try:
                    if productSkinName not in path:
                        path.insert(path.index('custom') + 1, productSkinName)
                except ValueError:
                    if productSkinName not in path:
                        path.append(productSkinName)
                path = ','.join(path)
                skinstool.addSkinSelection(skinName, path)


def install_types(self, out, types, package_name):
    typesTool = getToolByName(self, 'portal_types')
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
            # rr: explicitly catching 'simple item' because
            # CMF 2.0 removed the meta_type from the basic TIs :-(
            # seems to me, 'manage_addTypeInformation' is just broken
            fti_meta_type = 'Factory-based Type Information'
        try:
            typesTool.manage_addTypeInformation(fti_meta_type,
                                                id=klass.portal_type,
                                                typeinfo_name=typeinfo_name)
        except ValueError:
            print "failed to add '%s'" % klass.portal_type
            print "fti_meta_type = %s" % fti_meta_type
        # rr: from CMF-2.0 onward typeinfo_name from the call above
        # is ignored and we have to do some more work
        t, fti = _getFtiAndDataFor(
            typesTool, klass.portal_type, klass.__name__, package_name)
        if t and fti:
            t.manage_changeProperties(**fti)
            if 'aliases' in fti:
                t.setMethodAliases(fti['aliases'])

        # Set the human readable title explicitly
        if t:
            t.title = klass.archetype_name


def _getFtiAndDataFor(tool, typename, klassname, package_name):
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
        if fti['id'] == klassname:
            fti['content_meta_type'] = fti['meta_type']
            return t, fti
    return t, None


def install_actions(self, out, types):
    typesTool = getToolByName(self, 'portal_types')
    for portal_type in types:
        # rr: XXX TODO somehow the following doesn't do anymore what
        # it used to do :-(
        fixActionsForType(portal_type, typesTool)


def install_indexes(self, out, types):
    portal_catalog = catalog = getToolByName(self, 'portal_catalog')
    for cls in types:
        if 'indexes' not in cls.installMode:
            continue

        for field in cls.schema.fields():
            if not field.index:
                continue

            if isinstance(field.index, basestring):
                index = (field.index,)
            elif isinstance(field.index, (tuple, list)):
                index = field.index
            else:
                raise SyntaxError("Invalid Index Specification %r"
                                  % field.index)

            for alternative in index:
                installed = None
                index_spec = alternative.split(':', 1)
                use_column = 0
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
                    parts[0] = parts[0][str_idx + 1:]
                    catalog = getToolByName(self, catalog_name)
                else:
                    catalog = portal_catalog

                #####################
                # add metadata column

                # lets see if the catalog is itself an Archetype:
                isArchetype = IBaseObject.providedBy(catalog)
                # archetypes based zcatalogs need to provide a different method
                # to list its schema-columns to not conflict with archetypes
                # schema
                hasNewWayMethod = hasattr(catalog, 'zcschema')
                hasOldWayMethod = not isArchetype and hasattr(
                    catalog, 'schema')
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
                # if not parts[0]:
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
                        # Check for the index and add it if missing
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
    filtered_types = []

    for rti in types:
        t = rti['klass']

        isBaseObject = 0
        if IBaseObject.implementedBy(t):
            isBaseObject = 1
        else:
            for k in t.__bases__:
                if IBaseObject.implementedBy(k):
                    isBaseObject = 1
                    break

        if isBaseObject:
            filtered_types.append(t)
        else:
            print >> out, ("%s doesnt implements IBaseObject. "
                           "Possible misconfiguration. "
                           "Check if your class has an "
                           "'implements(IBaseObject)' "
                           "(or IBaseContent, or IBaseFolder)" % repr(t))

    return filtered_types


def setupEnvironment(self, out, types,
                     package_name,
                     globals=types_globals,
                     product_skins_dir='skins',
                     require_dependencies=True,
                     install_deps=1):

    if install_deps:
        qi = getToolByName(self, 'portal_quickinstaller', None)
        if require_dependencies:
            if not qi.isProductInstalled('CMFFormController'):
                qi.installProduct('CMFFormController', locked=1)
                print >>out, 'Installing CMFFormController'
            if not qi.isProductInstalled('MimetypesRegistry'):
                qi.installProduct('MimetypesRegistry')
                print >>out, 'Installing MimetypesRegistry'
            if not qi.isProductInstalled('PortalTransforms'):
                qi.installProduct('PortalTransforms')
                print >>out, 'Installing PortalTransforms'
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

    typesTool = getToolByName(self, 'portal_types')
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


# The master installer
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
    # rr: sometimes the default actions are still missing
    doubleCheckDefaultTypeActions(self, ftypes)
    if refresh_references and ftypes:
        rc = getToolByName(self, REFERENCE_CATALOG)
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

    rc = getToolByName(self, REFERENCE_CATALOG)
    mt = tuple([t.meta_type for t in ftypes])

    # because manage_catalogFoundItems sucks we have to do it on our own ...
    func = rc.catalog_object
    obj = self
    path = '/'.join(obj.getPhysicalPath())
    REQUEST = self.REQUEST

    rc.ZopeFindAndApply(obj,
                        obj_metatypes=mt,
                        search_sub=1,
                        REQUEST=REQUEST,
                        apply_func=func,
                        apply_path=path)
