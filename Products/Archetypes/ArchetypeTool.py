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

from Products.Archetypes.ClassGen import generateClass, generateCtor, \
     generateZMICtor
from Products.Archetypes.SQLStorageConfig import SQLStorageConfig
from Products.Archetypes.config import TOOL_NAME, UID_CATALOG, HAS_GRAPHVIZ
from Products.Archetypes.debug import log
from Products.Archetypes.utils import findDict, DisplayList, mapply
from Products.Archetypes.Renderer import renderer

from AccessControl import ClassSecurityInfo
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
from ZODB.POSException import ConflictError
from Acquisition import ImplicitAcquisitionWrapper

class BoundPageTemplateFile(PageTemplateFile):

    def __init__(self, *args, **kw):
        self._extra = kw['extra']
        del kw['extra']
        args = (self,) + args
        mapply(PageTemplateFile.__init__, *args, **kw)

    def pt_render(self, source=0, extra_context={}):
        options = extra_context.get('options', {})
        options.update(self._extra)
        extra_context['options'] = options
        return PageTemplateFile.pt_render(self, source, extra_context)

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
_skins = os.path.join(os.path.dirname(__file__), 'skins')
_zmi = os.path.join(_www, 'zmi')
document_icon = os.path.join(_zmi, 'icons', 'document_icon.gif')
folder_icon = os.path.join(_zmi, 'icons', 'folder_icon.gif')

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
                       'action': 'string:${object_url}/reference_graph',
                       'condition': 'object/archetype_tool/has_graphviz',
                       'permissions': (CMFCorePermissions.View,),
                       'visible' : 1,
                       },
                     )
      }, )

def fixActionsForType(portal_type, typesTool):
    if 'actions' in portal_type.installMode:
        typeInfo = getattr(typesTool, portal_type.portal_type)
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
                # DM: "Expression" derives from "Persistent" and
                #  we must not put persistent objects into class attributes.
                #  Thus, copy "action"
                action = action.copy()
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
    fti[0]['factory']     = "add%s" % klass.__name__
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

        ctor = getattr(module, "add%s" % typeName, None)
        if ctor is None:
            ctor = generateCtor(typeName, module)

        content_types += (klass,)
        constructors  += (ctor,)
        ftis   += fti

    return content_types, constructors, ftis


_types = {}

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
        'name'  : klass.__name__,
        'identifier': klass.meta_type.capitalize().replace(' ', '_'),
        'meta_type': klass.meta_type,
        'portal_type': klass.portal_type,
        'package' : package,
        'module' : sys.modules[klass.__module__],
        'schema' : klass.schema,
        'signature' : klass.schema.signature(),
        # backward compatibility, remove later
        'type' : klass.schema,
        }

    key = "%s.%s" % (package, data['meta_type'])
    if key in _types.keys():
        existing = _types[key]
        existing_name = '%s.%s' % (existing['module'].__name__, existing['name'])
        override_name = '%s.%s' % (data['module'].__name__, data['name'])
        zLOG.LOG('ArchetypesTool', zLOG.WARNING, ('Trying to register "%s" which '
                 'has already been registered.  The new type %s '
                 'is going to override %s') % (key, override_name, existing_name))
    _types[key] = data

def fixAfterRenameType(context, old_portal_type, new_portal_type):
    """Helper method to fix some vars after renaming a type in portal_types
    
    It will raise an IndexError if called with a nonexisting old_portal_type. 
    If you like to swallow the error please use a try/except block in your own
    code and do NOT 'fix' this method.
    """
    at_tool = getToolByName(context, TOOL_NAME)
    __traceback_info__ = (context, old_portal_type, new_portal_type,
                          [ t['portal_type'] for t in _types.values() ] )
    # will fail if old portal type wasn't registered (DO 'FIX' THE INDEX ERROR!)
    old_type = [t for t in _types.values()
                if t['portal_type'] == old_portal_type][0]

    # rename portal type
    old_type['portal_type'] = new_portal_type

    # copy old templates to new portal name without references
    old_templates = at_tool._templates.get(old_portal_type)
    at_tool._templates[new_portal_type] = deepcopy(old_templates)

def registerClasses(context, package, types=None):
    registered = listTypes(package)
    if types is not None:
        registered = filter(lambda t: t['meta_type'] in types, registered)
    for t in registered:
        module = t['module']
        typeName = t['name']
        meta_type = t['meta_type']
        portal_type = t['portal_type']
        klass = t['klass']
        ctorName = "manage_add%s" % typeName
        constructor = getattr(module, ctorName, None)
        if constructor is None:
            constructor = generateZMICtor(typeName, module)
        addFormName = "manage_add%sForm" % typeName
        setattr(module, addFormName,
                BoundPageTemplateFile('base_add.pt', _zmi,
                                      __name__=addFormName,
                                      extra={'constructor':ctorName,
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))
        editFormName = "manage_edit%sForm" % typeName
        setattr(klass, editFormName,
                BoundPageTemplateFile('base_edit.pt', _zmi,
                                      __name__=editFormName,
                                      extra={'handler':'processForm',
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))

        position = 0
        for item in klass.manage_options:
            if item['label'] != 'Contents':
                continue
            position += 1
        folderish = getattr(klass, 'isPrincipiaFolderish', position)
        options = list(klass.manage_options)
        options.insert(position, {'label' : 'Edit',
                                  'action' : editFormName
                                  })
        klass.manage_options = tuple(options)
        generatedForm = getattr(module, addFormName)
        context.registerClass(
            t['klass'],
            constructors=(generatedForm,
                          constructor),
            visibility=None,
            icon=folderish and folder_icon or document_icon,
            )

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
        # DM (avoid persistency bug): "_types" now maps known schemas to signatures
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
    def listRegisteredTypes(self, inProject=None):
        """Return the list of sorted types"""
        tt = getToolByName(self, "portal_types")
        def isRegistered(type, tt=tt):
            return tt.getTypeInfo(type['portal_type']) != None

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
            if t['meta_type'] == type:
                # We have to return the schema wrapped into the acquisition of
                # something to allow access. Otherwise we will end up with:
                # Your user account is defined outside the context of the object
                # being accessed.
                t['schema'] = ImplicitAcquisitionWrapper(t['schema'], self)
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
                instance = t('')
                wrapped = instance.__of__(context)
                if isinstance(wrapped, DefaultDublinCoreImpl):
                    DefaultDublinCoreImpl.__init__(wrapped)
                wrapped._is_fake_instance = 1
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
                    field.required = 0
                    field.addable = 0 # for ReferenceField
                    if not isinstance(field.vocabulary, DisplayList):
                        field.vocabulary = field.Vocabulary(instance)
                    if '' not in field.vocabulary.keys():
                        field.vocabulary = DisplayList([('', '<any>')]) + \
                                           field.vocabulary
                    widget.populate = 0
                    field_name = field.accessor
                    accessor = field.getDefault

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
        allTypes = _types.copy(); allTypes.update(self._types)
        return allTypes.keys()

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'getChangedSchema')
    def getChangedSchema(self):
        """Returns a list of tuples indicating which schema have changed.
           Tuples have the form (schema, changed)"""
        list = []
        currentTypes = _types
        ourTypes = self._types; modified = 0
        keys = self._listAllTypes()
        keys.sort()
        for t in keys:
            if t not in ourTypes:
                # add it
                ourTypes[t] = currentTypes[t]['signature']; modified = 1
                list.append((t, 0))
            elif t not in currentTypes:
                # huh: what shall we do? We remove it -- this might be wrong!
                del ourTypes[t]; modified = 1
                # we do not add an entry because we cannot update
                # these objects (having no longer type information for them)
            else:
                list.append((t, ourTypes[t] != currentTypes[t]['signature']))
        if modified: self._p_changed = 1
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
                if REQUEST.form.get(t, 0):
                    update_types.append(t)
            update_all = REQUEST.form.get('update_all', 0)

        # XXX: Enter this block only when there are types to update!
        if update_types:
            # Use the catalog's ZopeFindAndApply method to walk through
            # all objects in the portal.  This works much better than
            # relying on the catalog to find objects, because an object
            # may be uncatalogable because of its schema, and then you
            # can't update it if you require that it be in the catalog.
            catalog = getToolByName(self, 'portal_catalog')
            portal = getToolByName(self, 'portal_url').getPortalObject()
            meta_types = [_types[t]['meta_type'] for t in update_types]
            if update_all:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=1, apply_func=self._updateObject)
            else:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=1, apply_func=self._updateChangedObject)
            for t in update_types:
                self._types[t] = _types[t]['signature']
            self._p_changed = 1
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
           dictionary... returns 1 or 0 so it can be used within a lambda as
           the predicate for a filterFields call"""
        vis_dict = field.widget.visible
        value = ""
        if vis_dict.has_key(vis_key):
            value = field.widget.visible[vis_key]
        if value==vis_value:
            return 1
        else:
            return 0

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
