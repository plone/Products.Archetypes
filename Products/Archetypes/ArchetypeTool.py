from __future__ import nested_scopes

import os.path
import sys
from copy import deepcopy
from types import StringType, StringTypes
from md5 import md5
from DateTime import DateTime
from StringIO import StringIO

from Products.Archetypes.interfaces.base import IBaseObject, IBaseFolder
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata

from Products.Archetypes.ClassGen import generateClass, generateCtor
from Products.Archetypes.SQLStorageConfig import SQLStorageConfig
from Products.Archetypes.config  import PKG_NAME, TOOL_NAME, UID_CATALOG
from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.utils import capitalize, findDict, DisplayList, unique
from Products.Archetypes.Renderer import renderer
from Products.Archetypes.Schema import getAxisManager

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Globals import InitializeClass, PersistentMapping
from OFS.Folder import Folder
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.interfaces.portal_catalog \
     import portal_catalog as ICatalogTool
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.ZCatalog.IZCatalog import IZCatalog
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression


try:
    from Products.CMFPlone.Configuration import getCMFVersion
except ImportError:
    # Configuration and getCMFVersion come with Plone 2.0
    def getCMFVersion():
        from os.path import join
        from Globals import package_home
        from Products.CMFCore import cmfcore_globals
        path=join(package_home(cmfcore_globals),'version.txt')
        file=open(path, 'r')
        _version=file.read()
        file.close()
        return _version.strip()

_www = os.path.join(os.path.dirname(__file__), 'www')

# This is the template that we produce our custom types from
# Never actually used
base_factory_type_information = (
    { 'id': 'Archetype'
      , 'content_icon': 'document_icon.gif'
      , 'meta_type': 'Archetype'
      , 'description': ( 'Archetype for flexible types')
      , 'product': 'Unknown Package'
      , 'factory': 'addContent'
      , 'immediate_view': 'base_edit'
      , 'global_allow': 1
      , 'filter_content_types': 0
      , 'actions': (
                     { 'id': 'view',
                       'name': 'View',
                       'action': 'string:${object_url}/base_view',
                       'permissions': (CMFCorePermissions.View,),
                       },

                     { 'id': 'edit',
                       'name': 'Edit',
                       'action': 'string:${object_url}/base_edit',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'metadata',
                       'name': 'Properties',
                       'action': 'string:${object_url}/base_metadata',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'references',
                       'name': 'References',
                       'action': 'string:${object_url}/reference_edit',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       'visible' : 0,
                       },

                     { 'id' : 'ttw_schema',
                       'name' : 'Schema Management',
                       'action' : 'string:${object_url}/schema_editor',
                       'permissions' : (CMFCorePermissions.ManagePortal,),
                       'visible': 1,
                       'condition' : 'python: object.archetype_tool.getProvidedSchema(object) is not None',
                       },
                     )
      }, )

def fixActionsForType(portal_type, typesTool):
    if 'actions' in portal_type.installMode:
        typeInfo = getattr(typesTool, portal_type.__name__)
        if hasattr(portal_type, 'actions'):
            # Look for each action we define in portal_type.actions in
            # typeInfo.action replacing it if its there and just
            # adding it if not
            if getattr(portal_type,'include_default_actions', 1):
                new = list(typeInfo._actions)
            else:
                # If no standard actions are wished -
                # dont display them
                new=[]

            cmfver=getCMFVersion()

            for action in portal_type.actions:
                if cmfver[:7] >= "CMF-1.4" or cmfver == 'Unreleased':
                    # Then we know actions are defined new style as
                    # ActionInformations
                    hits = [a for a in new if a.id==action['id']]

                    # Change action and condition into expressions, if
                    # they are still strings
                    if action.has_key('action') and \
                           type(action['action']) in (type(''), type(u'')):
                        action['action']=Expression(action['action'])
                    if action.has_key('condition') and \
                           type(action['condition']) in (type(''), type(u'')):
                        action['condition']=Expression(action['condition'])
                    if hits:
                        hits[0].__dict__.update(action)
                    else:
                        if action.has_key('name'):
                            action['title']=action['name']
                            del action['name']

                        new.append (ActionInformation(**action))
                else:
                    hit = findDict(new, 'id', action['id'])
                    if hit:
                        hit.update(action)
                    else:
                        new.append(action)

            # Update Aliases
            if cmfver[:7] >= "CMF-1.4" or cmfver == 'Unreleased':
                if (hasattr(portal_type,'aliases') and
                    hasattr(typeInfo, 'setMethodAliases')):
                    typeInfo.setMethodAliases(portal_type.aliases)
                else:
                    # Custom views might need to reguess the aliases
                    if hasattr(typeInfo,'_guessMethodAliases'):
                        typeInfo._guessMethodAliases()

            typeInfo._actions = tuple(new)
            typeInfo._p_changed = 1

        if hasattr(portal_type,'factory_type_information'):
            typeInfo.__dict__.update(portal_type.factory_type_information)
            typeInfo._p_changed = 1


def modify_fti(fti, klass, pkg_name):
    fti[0]['id']          = klass.__name__
    fti[0]['meta_type']   = klass.meta_type
    fti[0]['description'] = klass.__doc__
    fti[0]['factory']     = "add%s" % capitalize(klass.__name__)
    fti[0]['product']     = pkg_name

    if hasattr(klass, "content_icon"):
        fti[0]['content_icon'] = klass.content_icon

    if hasattr(klass, "global_allow"):
        allow = klass.global_allow
        fti[0]['global_allow'] = allow

    if hasattr(klass, "allowed_content_types"):
        allowed = klass.allowed_content_types
        fti[0]['allowed_content_types'] = allowed
        fti[0]['filter_content_types'] = allowed and 1 or 0

    if hasattr(klass, "filter_content_types"):
        filter = klass.filter_content_types
        fti[0]['filter_content_types'] = filter

    if hasattr(klass, "immediate_view"):
        fti[0]['immediate_view'] = klass.immediate_view

    if not IReferenceable.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'references')
        refs['visible'] = 0

    if not IExtensibleMetadata.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'metadata')
        refs['visible'] = 0

def process_types(types, pkg_name):
    content_types = ()
    constructors  = ()
    ftis          = ()

    for rti in types:
        typeName = rti['name']
        klass  = rti['klass']
        module = rti['module']

        if hasattr(module, "factory_type_information"):
            fti = module.factory_type_information
        else:
            fti = deepcopy(base_factory_type_information)
            modify_fti(fti, klass, pkg_name)

        # Add a callback to modifty the fti
        if hasattr(module, "modify_fti"):
            module.modify_fti(fti[0])
        else:
            m = None
            for k in klass.__bases__:
                base_module = sys.modules[k.__module__]
                if hasattr(base_module, "modify_fti"):
                    m = base_module
                    break
            if m is not None:
                m.modify_fti(fti[0])

        ctor = getattr(module, "add%s" % capitalize(typeName),
                         None)
        if ctor is None:
            ctor = generateCtor(typeName, module)

        content_types += (klass,)
        constructors  += (ctor,)
        ftis   += fti

    return content_types, constructors, ftis


_types = {}
_types_callback = []

def _guessPackage(base):
    if base.startswith('Products'):
        base = base[9:]
        idx = base.index('.')
        if idx != -1:
            base = base[:idx]
    return base

def registerType(klass, package=None):
    if not package: package = _guessPackage(klass.__module__)

    ## registering a class results in classgen doing its thing
    ## Set up accessor/mutators and sane meta/portal_type
    generateClass(klass)

    data = {
        'klass' : klass,
        'name'  : klass.meta_type,
        'portal_type': klass.portal_type,
        'package' : package,
        'module' : sys.modules[klass.__module__],
        'schema' : klass.schema,
        'signature' : klass.schema.signature(),
        # backward compatibility, remove later
        'type' : klass.schema,
        }

    key = "%s.%s" % (package, klass.meta_type)
    _types[key] = data

    for tc in _types_callback:
        tc(klass, package)


def listTypes(package=None):
    values = _types.values()
    if package:
        values = [v for v in values if v['package'] == package]

    return values

def getType(name, package):
    key = "%s.%s" % (package, name)
    return _types[key]

class WidgetWrapper:
    """ Wrapper used for drawing widgets without an instance (for ex.,
    for a search form) """

    security = ClassSecurityInfo()
    security.declareObjectPublic()
    def __init__(self, **args):
        self._args = args

    def __call__(self):
        __traceback_info__ = self._args
        return renderer.render(**self._args)

last_load = DateTime()

class ArchetypeTool(UniqueObject, ActionProviderBase, \
                    SQLStorageConfig, Folder):
    """ Archetypes tool, manage aspects of Archetype instances """
    id        = TOOL_NAME

    meta_type = TOOL_NAME.title().replace('_', ' ')

    isPrincipiaFolderish = 1 # Show up in the ZMI

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
        self._types = {}
        for k, t in _types.items():
            self._types[k] = {'signature':t['signature'], 'update':1}
        cb = lambda klass, package:self.registerType(klass, package)
        _types_callback.append(cb)
        self.last_types_update = DateTime()

        # SchemaProvider Data
        self._initSchemaProviderSystem()

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
        obj = self.unrestrictedTraverse(template, None)
        if obj:
            if not name:
                name = obj.title_or_id()
        else:
            name = template

        self._registeredTemplates[template] = name


    security.declareProtected(CMFCorePermissions.View,
                              'lookupTemplates')
    def lookupTemplates(self, instance=None):
        results = []
        if type(instance) is not StringType:
            instance = instance.portal_type
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

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'bindTemplate')
    def bindTemplate(self, meta_type, templateList):
        """create binding between a type and its associated views"""
        self._templates[meta_type] = templateList

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
    def listRegisteredTypes(self, inProject=None):
        """Return the list of sorted types"""
        tt = getToolByName(self, "portal_types")
        def isRegistered(type, tt=tt):
            return tt.getTypeInfo(type['name']) != None

        def type_sort(a, b):
            v = cmp(a['package'], b['package'])
            if v != 0: return v
            c = cmp(a['klass'].__class__.__name__,
                    b['klass'].__class__.__name__)

            if c == 0:
                return cmp(a['package'], b['package'])
            return c

        values = listTypes()
        values.sort(type_sort)
        if inProject:
            values = [v for v in values if isRegistered(v)]

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
            if t['name'] == type:
                return t
        return None

    security.declareProtected(CMFCorePermissions.View,
                              'getSchema')
    def getSchema(self, sid):
        return self._schemas[sid]

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_installType')
    def manage_installType(self, typeName, package=None,
                           uninstall=None, REQUEST=None):
        """un/install a type ttw"""
        typesTool = getToolByName(self, 'portal_types')
        try:
            typesTool._delObject(typeName)
        except:
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
                              typeDesc['name'])


        # and update the actions as needed
        fixActionsForType(typeDesc['klass'], typesTool)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_debugForm")



    security.declarePublic('getSearchWidgets')
    def getSearchWidgets(self, package=None, type=None, context=None):
        """empty widgets for searching"""

        # possible problem: assumes fields with same name can be
        # searched with the same widget
        widgets = {}
        context = context is None and context or self
        for t in self.listTypes(package, type):
            instance = t('fake')
            instance = instance.__of__(context)
            if isinstance(instance, DefaultDublinCoreImpl):
                DefaultDublinCoreImpl.__init__(instance)
            instance._is_fake_instance = 1
            schema = instance.schema = instance.Schema().copy()
            fields = [f for f in schema.fields()
                      if (not widgets.has_key(f.getName())
                          and f.index and f.accessor)]
            for field in fields:
                field.required = 0
                field.addable = 0 # for ReferenceField
                if not isinstance(field.vocabulary, DisplayList):
                    field.vocabulary = field.Vocabulary(instance)
                if '' not in field.vocabulary.keys():
                    field.vocabulary = DisplayList([('', '<any>')]) + \
                                       field.vocabulary
                widget = field.widget
                widget.populate = 0
                widgets[field.getName()] = WidgetWrapper(
                    field_name=field.accessor,
                    mode='search',
                    widget=field.widget,
                    instance=instance,
                    field=field,
                    accessor=field.getDefault)
        widgets = widgets.items()
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


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'getChangedSchema')
    def getChangedSchema(self):
        """Returns a list of tuples indicating which schema have changed.
           Tuples have the form (schema, changed)"""
        list = []
        keys = self._types.keys()
        keys.sort()
        for t in keys:
            list.append((t, self._types[t]['update']))
        return list


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_updateSchema')
    def manage_updateSchema(self, REQUEST=None):
        """Make sure all objects' schema are up to date"""

        out = StringIO()
        print >> out, 'Updating schema...'

        update_types = []
        if REQUEST is None:
            for t in self._types.keys():
                if self._types[t]['update']:
                    update_types.append(t)
            update_all = 0
        else:
            for t in self._types.keys():
                if REQUEST.form.get(t, 0):
                    update_types.append(t)
            update_all = REQUEST.form.get('update_all', 0)

        # Use the catalog's ZopeFindAndApply method to walk through
        # all objects in the portal.  This works much better than
        # relying on the catalog to find objects, because an object
        # may be uncatalogable because of its schema, and then you
        # can't update it if you require that it be in the catalog.
        catalog = getToolByName(self, 'portal_catalog')
        portal = getToolByName(self, 'portal_url').getPortalObject()
        meta_types = [_types[t]['name'] for t in update_types]
        if update_all:
            catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                search_sub=1, apply_func=self._updateObject)
        else:
            catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                search_sub=1, apply_func=self._updateChangedObject)
        for t in update_types:
            self._types[t]['update'] = 0
        self._p_changed = 1
        return out.getvalue()

    def _updateObject(self, o, path):
        sys.stdout.write('updating %s\n' % o.getId())
        o._updateSchema()

    def _updateChangedObject(self, o, path):
        if not o._isSchemaCurrent():
            o._updateSchema()

    def __setstate__(self, v):
        """Add a callback to track product registrations"""
        ArchetypeTool.inheritedAttribute('__setstate__')(self, v)
        global _types
        global _types_callback
        if hasattr(self, '_types'):
            if not hasattr(self, 'last_types_update') or \
                   self.last_types_update.lessThan(last_load):
                for k, t in _types.items():
                    if self._types.has_key(k):
                        update = (t['signature'] !=
                                  self._types[k]['signature'])
                    else:
                        update = 1
                    self._types[k] = {'signature':t['signature'],
                                      'update':update}
                cb = lambda klass, package:self.registerType(klass, package)
                _types_callback.append(cb)
                self.last_types_update = DateTime()


    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'registerType')
    def registerType(self, klass, package):
        """This gets called every time registerType is called as soon as the
        hook is installed by setstate"""
        # See if the schema has changed.  If it has, flag it
        update = 0
        sig = klass.schema.signature()
        key = "%s.%s" % (package, klass.meta_type)
        old_data = self._types.get(key, None)
        if old_data:
            update = old_data.get('update', 0)
            old_sig = old_data.get('signature', None)
            if sig != old_sig:
                update = 1
        self._types[key] = {'signature':sig, 'update':update}
        self._p_changed = 1


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
            names = self.catalog_map.get(meta_type, ['portal_catalog',
                                                     UID_CATALOG])
        else:
            names = ['portal_catalog', UID_CATALOG]
        for name in names:
            try:
                catalogs.append(getToolByName(self, name))
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

    def lookupObject(self,uid):
        import warnings
        warnings.warn('ArchetypeTool.lookupObject is dreprecated',
                      DeprecationWarning)
        return self.reference_catalog.lookupObject(uid)

    getObject=lookupObject


    ## Schema Provider Hooks
    ##
    def _initSchemaProviderSystem(self):
        """So I can call it in migration"""

        #if not hasattr(self, "_schemasAxes"):
        self._schemaAxes = PersistentMapping()

        #if not hasattr(self, "_policyMementos"):
        self._policyMementos = PersistentMapping()

        #if not hasattr(self, "_axisMementos"):
        self._axisMementos = PersistentMapping()



    ## Axis management
    def registerSchemaAxis(self, axis):
        """
        Register an axis for providing schema
        """
        axisInstance = axis()
        name = axisInstance.getId()
        if not self._axisMementos.has_key(name):
            memento = axisInstance.register(self)
            self._axisMementos[name] = memento
        self._schemaAxes[name] = axisInstance

    def getSchemaAxisNames(self):
        """
        Get all the names axis configured for this tool.
        `getSchemaAxis` can lazy bind from the global registry
        based on these names
        """
        return self._schemaAxes.keys()

    def getSchemaAxis(self, name):
        """
        Load and regsiter a collector for this tool.
        This falls back to the global module level registry
        but calls register for this axis and this tool.
        """
        axis = self._schemaAxes.get(name)
        if not axis:
            axis = getCollectionStrategy(name)
            self.registerSchemaAxis(axis)
        return axis

    def provideSchema(self, axisName, schema, *args, **kwargs):
        """
        register a schema under an axis, we don't know what a axis
        keys off of so the interface is generic
        """
        axis = self.getSchemaAxis(axisName)
        memento = self._getAxisMemento(axisName)
        # Store a copy of the schema as we need to annotate its
        # fields with its key in this axis (as a function of the axis)
        schema = schema.copy()
        axis.provide(memento, schema, *args, **kwargs)

    ## Memento Code
    def _getAxisMemento(self, axis):
        """Return an object handled by an axis manager"""
        return self._axisMementos[axis]

    def _getPolicyMemento(self, policy):
        """Return an object used to drive a policy at runtime and
        scoped to a portal
        """
        memento = self._policyMementos.get(policy)
        if memento is None:
            memento = PersistentMapping()
            self._policyMementos[policy] = memento
        return memento



InitializeClass(ArchetypeTool)
