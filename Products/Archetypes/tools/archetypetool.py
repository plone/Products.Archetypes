from __future__ import nested_scopes

import os.path
import sys
from copy import deepcopy
from types import StringType
from DateTime import DateTime
from StringIO import StringIO

from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.lib.classgen import generateClass
from Products.Archetypes.lib.classgen import generateCtor
from Products.Archetypes.lib.classgen import generateZMICtor
from Products.Archetypes.storage.sql.config import SQLStorageConfig
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import HAS_GRAPHVIZ
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.utils import findDict
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.renderer import renderService
from Products.Archetypes.registry.typeregistry import typeRegistry
from Products.Archetypes.lib.register import listTypes

from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.interfaces.portal_catalog \
     import portal_catalog as ICatalogTool
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression

from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from Globals import InitializeClass
from Globals import PersistentMapping
from OFS.Folder import Folder
from Products.ZCatalog.IZCatalog import IZCatalog
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.POSException import ConflictError


class BoundPageTemplateFile(PageTemplateFile):

    def __init__(self, *args, **kw):
        self._extra = kw['extra']
        del kw['extra']
        args = (self,) + args
        mapply(PageTemplateFile.__init__, *args, **kw)

    def pt_render(self, source=False, extra_context={}):
        options = extra_context.get('options', {})
        options.update(self._extra)
        extra_context['options'] = options
        return PageTemplateFile.pt_render(self, source, extra_context)


_www = os.path.join(os.path.dirname(__file__), 'www')
_skins = os.path.join(os.path.dirname(__file__), 'skins')
_zmi = os.path.join(_www, 'zmi')
document_icon = os.path.join(_zmi, 'icons', 'document_icon.gif')
folder_icon = os.path.join(_zmi, 'icons', 'folder_icon.gif')

class WidgetWrapper:
    """ Wrapper used for drawing widgets without an instance (for ex.,
    for a search form) """

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    def __init__(self, **args):
        self._args = args

    def __call__(self):
        __traceback_info__ = self._args
        return renderService.render(**self._args)

last_load = DateTime()

class ArchetypeTool(UniqueObject, ActionProviderBase, \
                    SQLStorageConfig, Folder):
    """ Archetypes tool, manage aspects of Archetype instances """
    id        = TOOL_NAME

    meta_type = TOOL_NAME.title().replace('_', ' ')

    isPrincipiaFolderish = True # Show up in the ZMI

    security = ClassSecurityInfo()

    meta_types = all_meta_types = ()

    manage_options=(
        (
        { 'label'  : 'Types',
          'action' : 'manage_debugForm',
          },

        {  'label'  : 'Catalogs',
           'action' : 'manage_catalogs',
           },

        { 'label'  : 'Templates',
          'action' : 'manage_templateForm',
          },

        {  'label'  : 'UIDs',
           'action' : 'manage_uids',
           },

        { 'label'  : 'Update Schema',
          'action' : 'manage_updateSchemaForm',
          },

        { 'label'  : 'Migration',
          'action' : 'manage_migrationForm',
          },

        )  + SQLStorageConfig.manage_options
        )

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_uids')
    manage_uids = PageTemplateFile('viewContents', _www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_templateForm')
    manage_templateForm = PageTemplateFile('manageTemplates',_www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_debugForm')
    manage_debugForm = PageTemplateFile('generateDebug', _www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_updateSchemaForm')
    manage_updateSchemaForm = PageTemplateFile('updateSchemaForm', _www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_migrationForm')
    manage_migrationForm = PageTemplateFile('migrationForm', _www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_dumpSchemaForm')
    manage_dumpSchemaForm = PageTemplateFile('schema', _www)
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_catalogs')
    manage_catalogs = PageTemplateFile('manage_catalogs', _www)



    def __init__(self):
        self._schemas = PersistentMapping()
        self._templates = PersistentMapping()
        self._registeredTemplates = PersistentMapping()
        # meta_type -> [names of CatalogTools]
        self.catalog_map = PersistentMapping()
        self.catalog_map['Reference'] = [] # References not in portal_catalog
        self._types = {}

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_dumpSchema')
    def manage_dumpSchema(self, REQUEST=None):
        """XML Dump Schema of passed in class"""
        from Products.Archetypes.Schema import getSchemata
        package = REQUEST.get('package', '')
        type_name = REQUEST.get('type_name', '')
        spec = self.getTypeSpec(package, type_name)
        type = self.lookupType(package, type_name)
        options = {}
        options['classname'] = spec
        options['schematas'] = getSchemata(type['klass'])
        REQUEST.RESPONSE.setHeader('Content-Type', 'text/xml')
        return self.manage_dumpSchemaForm(**options)

    ## Template Management
    ## Views can be pretty generic by iterating the schema so we don't
    ## register by type anymore, we just create per site selection
    ## lists
    ##
    ## we keep two lists, all register templates and their
    ## names/titles and the mapping of type to template bindings both
    ## are persistent
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'registerTemplate')
    def registerTemplate(self, template, name=None):
        # Lookup the template by name
        if not name:
            obj = self.unrestrictedTraverse(template, None)
            try:
                name = obj.title_or_id()
            except:
                name = template

        self._registeredTemplates[template] = name


    security.declareProtected(CMFCorePermissions.View,
                              'lookupTemplates')
    def lookupTemplates(self, instance=None):
        """
        lookup templates by giving an instance or a portal_type 
        returns a DisplayList 
        """        
        results = []
        if type(instance) is not StringType:
            instance = instance.meta_type
        try:
            templates = self._templates[instance]
        except KeyError:
            return DisplayList()
            # XXX look this up in the types tool later
            # self._templates[instance] = ['base_view',]
            # templates = self._templates[instance]
        for t in templates:
            results.append((t, self._registeredTemplates[t]))

        return DisplayList(results).sortedByValue()

    security.declareProtected(CMFCorePermissions.View,
                              'listTemplates')
    def listTemplates(self):
        """list all the templates"""
        return DisplayList(self._registeredTemplates.items()).sortedByValue()
    
    security.declareProtected(CMFCorePermissions.View,
                              'isTemplateEnabled')
    def isTemplateEnabled(self, type):
        """checks if an type uses ITemplateMixin"""
        # XXX this should check if ITemplateMixin is implemented
        return type['schema'].has_key('layout')

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'bindTemplate')
    def bindTemplate(self, portal_type, templateList):
        """create binding between a type and its associated views"""
        self._templates[portal_type] = templateList

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_templates')
    def manage_templates(self, REQUEST=None):
        """set all the template/type mappings"""
        prefix = 'template_names_'
        for key in REQUEST.form.keys():
            if key.startswith(prefix):
                k = key[len(prefix):]
                v = REQUEST.form.get(key)
                self.bindTemplate(k, v)

        add = REQUEST.get('addTemplate')
        name = REQUEST.get('newTemplate')
        if add and name:
            self.registerTemplate(name)

        return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_templateForm")

    ## Type/Schema Management
    security.declareProtected(CMFCorePermissions.View,
                              'listRegisteredTypes')
    def listRegisteredTypes(self, inProject=False):
        """Return the list of sorted types"""        

        def type_sort(a, b):
            v = cmp(a['package'], b['package'])
            if v != False: return v
            c = cmp(a['klass'].__class__.__name__,
                    b['klass'].__class__.__name__)

            if c == False:
                return cmp(a['package'], b['package'])
            return c

        values = listTypes()
        values.sort(type_sort)

        if inProject:
            # portal_type can change (as it does after ATCT-migration), so we
            # need to check against the content_meta_type of each type-info       
            tt = getToolByName(self, "portal_types")     
            meta_types= tt.listContentTypes(self, by_metatype=True)
            values = [v for v in values if v['portal_type'] in meta_types]

        return values


    security.declareProtected(CMFCorePermissions.View,
                              'getTypeSpec')
    def getTypeSpec(self, package, type):
        t = self.lookupType(package, type)
        module = t['klass'].__module__
        klass = t['name']
        return '%s.%s' % (module, klass)

    security.declareProtected(CMFCorePermissions.View,
                              'listTypes')
    def listTypes(self, package=None, type=None):
        """just the class"""
        if type is None:
            return [t['klass'] for t in listTypes(package)]
        else:
            return [getType(type, package)['klass']]

    security.declareProtected(CMFCorePermissions.View,
                              'lookupType')
    def lookupType(self, package, type):
        types = self.listRegisteredTypes()
        for t in types:
            if t['package'] != package: continue
            if t['meta_type'] == type:
                # We have to return the schema wrapped into the acquisition of
                # something to allow access. Otherwise we will end up with:
                # Your user account is defined outside the context of the object
                # being accessed.
                t['schema'] = ImplicitAcquisitionWrapper(t['schema'], self)
                return t
        return None

    # XXX unusable because nothing is writing to _schemas
    #security.declareProtected(CMFCorePermissions.View,
    #                          'getSchema')
    #def getSchema(self, sid):
    #    return self._schemas[sid]

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_installType')
    def manage_installType(self, typeName, package=None,
                           uninstall=None, REQUEST=None):
        """un/install a type ttw"""
        typesTool = getToolByName(self, 'portal_types')
        try:
            typesTool._delObject(typeName)
        except ConflictError:
            raise
        except: # XXX bare exception
            pass
        if uninstall is not None:
            if REQUEST:
                return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_debugForm")
            return

        typeinfo_name="%s: %s" % (package, typeName)

        # We want to run the process/modify_fti code which might not
        # have been called
        typeDesc = getType(typeName, package)
        process_types([typeDesc], package)

        typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                            id=typeName,
                                            typeinfo_name=typeinfo_name)
        t = getattr(typesTool, typeName, None)
        if t:
            t.title = getattr(typeDesc['klass'], 'archetype_name',
                              typeDesc['portal_type'])


        # and update the actions as needed
        fixActionsForType(typeDesc['klass'], typesTool)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_debugForm")



    security.declarePublic('getSearchWidgets')
    def getSearchWidgets(self, package=None, type=None, context=None, nosort=None):
        """Empty widgets for searching"""
        return self.getWidgets(package=package, type=type,
                               context=context, mode='search', nosort=nosort)

    security.declarePublic('getWidgets')
    def getWidgets(self, instance=None,
                   package=None, type=None,
                   context=None, mode='edit',
                   fields=None, schemata=None, nosort=None):
        """Empty widgets for standalone rendering"""

        widgets = []
        w_keys = {}
        context = context is None and context or self
        instances = instance is not None and [instance] or []
        f_names = fields
        if not instances:
            for t in self.listTypes(package, type):
                instance = t('fake_instance')
                instance._at_is_fake_instance = True
                # XXX _is_fake_instance will go away in AT 1.4
                instance._is_fake_instance = True
                wrapped = instance.__of__(context)
                wrapped.initializeArchetype()
                #if isinstance(wrapped, DefaultDublinCoreImpl):
                #    DefaultDublinCoreImpl.__init__(wrapped)
                instances.append(wrapped)
        for instance in instances:
            if schemata is not None:
                schema = instance.Schemata()[schemata].copy()
            else:
                schema = instance.Schema().copy()
            fields = schema.fields()
            if mode == 'search':
                # Include only fields which have an index
                # XXX duplicate fieldnames may break this,
                # as different widgets with the same name
                # on different schemas means only the first
                # one found will be used
                fields = [f for f in fields
                          if (f.accessor and
                              not w_keys.has_key(f.accessor)
                              and f.index)]
            if f_names is not None:
                fields = filter(lambda f: f.getName() in f_names, fields)
            for field in fields:
                widget = field.widget
                field_name = field.getName()
                accessor = field.getAccessor(instance)
                if mode == 'search':
                    field.required = False
                    field.addable = False # for ReferenceField
                    if not isinstance(field.vocabulary, DisplayList):
                        field.vocabulary = field.Vocabulary(instance)
                    if '' not in field.vocabulary.keys():
                        field.vocabulary = DisplayList([('', '<any>', 'at_search_any')]) + \
                                           field.vocabulary
                    widget.populate = False
                    field_name = field.accessor
                    # accessor must be a method which doesn't take an argument
                    # this lambda is facking an accessor
                    accessor = lambda: field.getDefault(instance)
    
                w_keys[field_name] = None
                widgets.append((field_name, WidgetWrapper(
                    field_name=field_name,
                    mode=mode,
                    widget=widget,
                    instance=instance,
                    field=field,
                    accessor=accessor)))
        if mode == 'search' and nosort == None:
            widgets.sort()
        return [widget for name, widget in widgets]

    security.declarePrivate('_rawEnum')
    def _rawEnum(self, callback, *args, **kwargs):
        """Finds all object to check if they are 'referenceable'"""
        catalog = getToolByName(self, 'portal_catalog')
        brains = catalog(id=[])
        for b in brains:
            o = b.getObject()
            if o is not None:
                if IBaseObject.isImplementedBy(o):
                    callback(o, *args, **kwargs)
            else:
                log("no object for brain: %s:%s" % (b,b.getURL()))


    security.declareProtected(CMFCorePermissions.View,
                              'enum')
    def enum(self, callback, *args, **kwargs):
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        for uid in keys:
            o = self.getObject(uid)
            if o:
                callback(o, *args, **kwargs)
            else:
                log("no object for %s" % uid)


    security.declareProtected(CMFCorePermissions.View,
                              'Content')
    def Content(self):
        """Return a list of all the content ids"""
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        results = catalog(UID=keys)
        return results


    ## Management Forms
    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_doGenerate')
    def manage_doGenerate(self, sids=(), REQUEST=None):
        """(Re)generate types """
        schemas = []
        for sid in sids:
            schemas.append(self.getSchema(sid))

        for s in schemas:
            s.generate()

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/manage_workspace")

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_inspect')
    def manage_inspect(self, UID, REQUEST=None):
        """dump some things about an object hook in the debugger for
        now"""
        object = self.getObject(UID)
        log(object, object.Schema(), dir(object))


        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         "/manage_uids"
                                         )

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_reindex')
    def manage_reindex(self, REQUEST=None):
        """assign UIDs to all basecontent objects"""

        def _index(object, archetype_tool):
            archetype_tool.registerContent(object)

        self._rawEnum(_index, self)

        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         "/manage_uids"
                                         )


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'index')
    index = manage_reindex


    def _listAllTypes(self):
        """list all types -- either currently known or known to us."""
        allTypes = typeRegistry.copy(); allTypes.update(self._types)
        return allTypes.keys()

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'getChangedSchema')
    def getChangedSchema(self):
        """Returns a list of tuples indicating which schema have changed.
           Tuples have the form (schema, changed)"""
        list = []
        currentTypes = typeRegistry
        ourTypes = self._types
        modified = False
        keys = self._listAllTypes()
        keys.sort()
        for t in keys:
            if t not in ourTypes:
                # add it
                ourTypes[t] = currentTypes[t]['signature']
                modified = True
                list.append((t, 0))
            elif t not in currentTypes:
                # huh: what shall we do? We remove it -- this might be wrong!
                del ourTypes[t]
                modified = True
                # we do not add an entry because we cannot update
                # these objects (having no longer type information for them)
            else:
                list.append((t, ourTypes[t] != currentTypes[t]['signature']))
        if modified:
            self._p_changed = True
        return list


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_updateSchema')
    def manage_updateSchema(self, REQUEST=None, update_all=None):
        """Make sure all objects' schema are up to date"""

        out = StringIO()
        print >> out, 'Updating schema...'

        update_types = []
        if REQUEST is None:
            # DM (avoid persistency bug): avoid code duplication
            update_types = [ti[0] for ti in self.getChangedSchema() if ti[1]]
        else:
            # DM (avoid persistency bug):
            for t in self._listAllTypes():
                if REQUEST.form.get(t, False):
                    update_types.append(t)
            update_all = REQUEST.form.get('update_all', False)

        # XXX: Enter this block only when there are types to update!
        if update_types:
            # Use the catalog's ZopeFindAndApply method to walk through
            # all objects in the portal.  This works much better than
            # relying on the catalog to find objects, because an object
            # may be uncatalogable because of its schema, and then you
            # can't update it if you require that it be in the catalog.
            catalog = getToolByName(self, 'portal_catalog')
            portal = getToolByName(self, 'portal_url').getPortalObject()
            meta_types = [typeRegistry[t]['meta_type'] for t in update_types]
            if update_all:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=True, apply_func=self._updateObject)
            else:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=True, apply_func=self._updateChangedObject)
            for t in update_types:
                self._types[t] = typeRegistry[t]['signature']
            self._p_changed = True
        return out.getvalue()

    # a counter to ensure that in a given interval a subtransaction commit is 
    # done.
    subtransactioncounter = 0
    
    def _updateObject(self, o, path):
        o._updateSchema()
        # subtransactions to avoid eating up RAM when used inside a 
        # 'ZopeFindAndApply' like in manage_updateSchema
        self.subtransactioncounter+=1
        # only every 250 objects a sub-commit, otherwise it eats up all diskspace
        if not self.subtransactioncounter % 250:
            get_transaction().commit(1) 

    def _updateChangedObject(self, o, path):
        if not o._isSchemaCurrent():
            self._updateObject(o, path)

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_updateSchema')
    def manage_migrate(self, REQUEST=None):
        """Run Extensions.migrations.migrate."""
        from Products.Archetypes.Extensions.migrations import migrate
        out = migrate(self)
        self.manage_updateSchema()
        return out

    # Catalog management
    security.declareProtected(CMFCorePermissions.View,
                              'listCatalogs')
    def listCatalogs(self):
        """show the catalog mapping"""
        return self.catalog_map


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_updateCatalogs')
    def manage_updateCatalogs(self, REQUEST=None):
        """set the catalog map for meta_type to include the list
        catalog_names"""
        prefix = 'catalog_names_'
        for key in REQUEST.form.keys():
            if key.startswith(prefix):
                k = key[len(prefix):]
                v = REQUEST.form.get(key)
                self.setCatalogsByType(k, v)

        return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_catalogs")

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'setCatalogsByType')
    def setCatalogsByType(self, meta_type, catalogList):
        self.catalog_map[meta_type] = catalogList


    security.declareProtected(CMFCorePermissions.View,
                              'getCatalogsByType')
    def getCatalogsByType(self, meta_type):
        """Return the catalog objects assoicated with a given type"""
        catalogs = []
        catalog_map=getattr(self,'catalog_map',None)
        if catalog_map:
            names = self.catalog_map.get(meta_type, ['portal_catalog',]
                                         )
        else:
            names = ['portal_catalog', ]
        for name in names:
            try:
                catalogs.append(getToolByName(self, name))
            except ConflictError:
                raise
            except Exception, E:
                log("No tool", name, E)
                pass
        return catalogs

    security.declareProtected(CMFCorePermissions.View,
                              'getCatalogsInSite')
    def getCatalogsInSite(self):
        """Return a list of ids for objects implementing ZCatalog"""
        root_objects = self.portal_url.getPortalObject().objectValues()
        res = []
        for object in root_objects:
            if ICatalogTool.isImplementedBy(object):
                res.append(object.getId())
                continue
            if IZCatalog.isImplementedBy(object):
                res.append(object.getId())
                continue

        res.sort()

        return res

    security.declareProtected(CMFCorePermissions.View, 'visibleLookup')
    def visibleLookup(self, field, vis_key, vis_value='visible'):
        """Checks the value of a specific key in the field widget's 'visible'
           dictionary... returns True or False so it can be used within a lambda as
           the predicate for a filterFields call"""
        vis_dict = field.widget.visible
        value = ""
        if vis_dict.has_key(vis_key):
            value = field.widget.visible[vis_key]
        if value==vis_value:
            return True
        else:
            return False

    def lookupObject(self,uid):
        import warnings
        warnings.warn('ArchetypeTool.lookupObject is dreprecated',
                      DeprecationWarning)
        return self.reference_catalog.lookupObject(uid)

    getObject=lookupObject


    def has_graphviz(self):
        """runtime check for graphviz, used in condition on tab"""
        return HAS_GRAPHVIZ

InitializeClass(ArchetypeTool)
