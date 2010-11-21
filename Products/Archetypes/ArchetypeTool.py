import os.path
import sys
from copy import deepcopy
from DateTime import DateTime
from StringIO import StringIO

from zope.interface import implements

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IExtensibleMetadata
from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.ITemplateMixin import ITemplateMixin
from Products.Archetypes.ClassGen import generateClass
from Products.Archetypes.ClassGen import generateCtor
from Products.Archetypes.ClassGen import generateZMICtor
from Products.Archetypes.SQLStorageConfig import SQLStorageConfig
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import HAS_GRAPHVIZ
from Products.Archetypes.log import log
from Products.Archetypes.utils import findDict
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import mapply
from Products.Archetypes.Renderer import renderer

from Products.CMFCore import permissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression

from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from App.class_init import InitializeClass
from Persistence import PersistentMapping
from OFS.Folder import Folder
from Products.ZCatalog.interfaces import IZCatalog
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.POSException import ConflictError
import transaction

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

# This is the template that we produce our custom types from
base_factory_type_information = (
    { 'id': 'Archetype'
      , 'content_icon': 'document_icon.gif'
      , 'meta_type': 'Archetype'
      , 'description': ('Archetype for flexible types')
      , 'product': 'Unknown Package'
      , 'factory': 'addContent'
      , 'immediate_view': 'base_edit'
      , 'global_allow': True
      , 'filter_content_types': False
      , 'allow_discussion': False
      , 'fti_meta_type' : FactoryTypeInformation.meta_type
      , 'aliases' : {'(Default)' : 'base_view',
                     'view' : '(Default)',
                     'index.html' : '(Default)',
                     'edit' : 'base_edit',
                     'properties' : 'base_metadata',
                     'gethtml' : '',
                     'mkdir' : '',
                     }
      , 'actions': (
                     { 'id': 'view',
                       'title': 'View',
                       'action': Expression('string:${object_url}/view'),
                       'permissions': (permissions.View,),
                       },

                     { 'id': 'edit',
                       'title': 'Edit',
                       'action': Expression('string:${object_url}/edit'),
                       'permissions': (permissions.ModifyPortalContent,),
                       'condition': Expression('not:object/@@plone_lock_info/is_locked_for_current_user')
                       },

                     { 'id': 'metadata',
                       'title': 'Properties',
                       'action': Expression('string:${object_url}/properties'),
                       'permissions': (permissions.ModifyPortalContent,),
                       },

                     )
      }, )

def fixActionsForType(portal_type, typesTool):
    if 'actions' in portal_type.installMode:
        typeInfo = getattr(typesTool, portal_type.portal_type, None)
        if typeInfo is None:
            return
        if hasattr(portal_type, 'actions'):
            # Look for each action we define in portal_type.actions in
            # typeInfo.action replacing it if its there and just
            # adding it if not
            ## rr: this is now trial-and-error programming
            ## I really don't know what's going on here
            ## most importantly I don't know why the default
            ## actions are not set in some cases :-(
            ## (maybe they are removed afterwards sometimes???)
            ## if getattr(portal_type,'include_default_actions', True):
            if True:
                default = [ActionInformation(**action) for action in
                           base_factory_type_information[0]['actions']]
                next = list(typeInfo._actions)
                all = next + default
                new = [a.clone() for a in all]
            else:
                # If no standard actions are wished don't display them
                new = []

            for action in portal_type.actions:
                # DM: "Expression" derives from "Persistent" and
                # we must not put persistent objects into class attributes.
                # Thus, copy "action"
                action = action.copy()
                hits = [a for a in new if a.id == action['id']]

                # Change action and condition into expressions, if
                # they are still strings
                if action.has_key('action') and \
                       type(action['action']) in (type(''), type(u'')):
                    action['action'] = Expression(action['action'])
                if action.has_key('condition') and \
                       type(action['condition']) in (type(''), type(u'')):
                    action['condition'] = Expression(action['condition'])
                if action.has_key('name'):
                    action['title'] = action['name']
                    del action['name']
                if hits:
                    hits[0].__dict__.update(action)
                else:
                    new.append(ActionInformation(**action))

            typeInfo._actions = tuple(new)
            typeInfo._p_changed = True

        if hasattr(portal_type, 'factory_type_information'):
            typeInfo.__dict__.update(portal_type.factory_type_information)
            typeInfo._p_changed = True


def modify_fti(fti, klass, pkg_name):
    fti[0]['id'] = klass.__name__
    fti[0]['meta_type'] = klass.meta_type
    fti[0]['description'] = klass.__doc__
    fti[0]['factory'] = 'add%s' % klass.__name__
    fti[0]['product'] = pkg_name

    if hasattr(klass, 'content_icon'):
        fti[0]['content_icon'] = klass.content_icon

    if hasattr(klass, 'global_allow'):
        fti[0]['global_allow'] = klass.global_allow

    if hasattr(klass, 'allow_discussion'):
        fti[0]['allow_discussion'] = klass.allow_discussion

    if hasattr(klass, 'allowed_content_types'):
        allowed = klass.allowed_content_types
        fti[0]['allowed_content_types'] = allowed
        fti[0]['filter_content_types'] = allowed and True or False

    if hasattr(klass, 'filter_content_types'):
        fti[0]['filter_content_types'] = klass.filter_content_types

    if hasattr(klass, 'immediate_view'):
        fti[0]['immediate_view'] = klass.immediate_view

    if not IExtensibleMetadata.implementedBy(klass):
        refs = findDict(fti[0]['actions'], 'id', 'metadata')
        refs['visible'] = False

    # Set folder_listing to 'view' if the class implements ITemplateMixin
    if not ITemplateMixin.implementedBy(klass):
        actions = []
        for action in fti[0]['actions']:
            if action['id'] != 'folderlisting':
                actions.append(action)
            else:
                action['action'] = 'string:${folder_url}/view'
                actions.append(action)
        fti[0]['actions'] = tuple(actions)

    # Remove folderlisting action from non folderish content types
    if not getattr(klass,'isPrincipiaFolderish', None):
        actions = []
        for action in fti[0]['actions']:
            if action['id'] != 'folderlisting':
                actions.append(action)
        fti[0]['actions'] = tuple(actions)

    # CMF 1.5 method aliases
    if getattr(klass, 'aliases', None):
        aliases = klass.aliases
        if not isinstance(aliases, dict):
            raise TypeError, "Invalid type for method aliases in class %s" % klass
        for required in ('(Default)', 'view',):
            if required not in aliases:
                raise ValueError, "Alias %s is required but not provied by %s" % (
                                  required, klass)
        fti[0]['aliases'] = aliases

    # Dynamic View FTI support
    if getattr(klass, 'default_view', False):
        default_view = klass.default_view
        if not isinstance(default_view, basestring):
            raise TypeError, "Invalid type for default view in class %s" % klass
        fti[0]['default_view'] = default_view
        fti[0]['view_methods'] = (default_view, )

        if getattr(klass, 'suppl_views', False):
            suppl_views = klass.suppl_views
            if not isinstance(suppl_views, (list, tuple)):
                raise TypeError, "Invalid type for suppl views in class %s" % klass
            if not default_view in suppl_views:
                suppl_views = suppl_views + (default_view, )
            fti[0]['view_methods'] = suppl_views
    if getattr(klass, '_at_fti_meta_type', False):
        fti[0]['fti_meta_type'] = klass._at_fti_meta_type
    else:
        if fti[0].get('fti_meta_type', False):
            klass._at_fti_meta_type = fti[0]['fti_meta_type']
        else:
            fti[0]['fti_meta_type'] = FactoryTypeInformation.meta_type


def process_types(types, pkg_name):
    content_types = ()
    constructors = ()
    ftis = ()

    for rti in types:
        typeName = rti['name']
        klass = rti['klass']
        module = rti['module']

        if hasattr(module, 'factory_type_information'):
            fti = module.factory_type_information
        else:
            fti = deepcopy(base_factory_type_information)
            modify_fti(fti, klass, pkg_name)

        # Add a callback to modifty the fti
        if hasattr(module, 'modify_fti'):
            module.modify_fti(fti[0])
        else:
            m = None
            for k in klass.__bases__:
                base_module = sys.modules[k.__module__]
                if hasattr(base_module, 'modify_fti'):
                    m = base_module
                    break
            if m is not None:
                m.modify_fti(fti[0])

        ctor = getattr(module, 'add%s' % typeName, None)
        if ctor is None:
            ctor = generateCtor(typeName, module)

        content_types += (klass,)
        constructors += (ctor,)
        ftis += fti

    return content_types, constructors, ftis


_types = {}

def registerType(klass, package):
    # Registering a class results in classgen doing its thing
    # Set up accessor/mutators and sane meta/portal_type
    generateClass(klass)

    data = {
        'klass' : klass,
        'name' : klass.__name__,
        'identifier': klass.meta_type.capitalize().replace(' ', '_'),
        'meta_type': klass.meta_type,
        'portal_type': klass.portal_type,
        'package' : package,
        'module' : sys.modules[klass.__module__],
        'schema' : klass.schema,
        'signature' : klass.schema.signature(),
        }

    key = '%s.%s' % (package, data['meta_type'])
    if key in _types.keys():
        existing = _types[key]
        existing_name = '%s.%s' % (existing['module'].__name__, existing['name'])
        override_name = '%s.%s' % (data['module'].__name__, data['name'])
        log('ArchetypesTool: Trying to register "%s" which ' \
            'has already been registered.  The new type %s ' \
            'is going to override %s' % (key, override_name, existing_name))
    _types[key] = data

def fixAfterRenameType(context, old_portal_type, new_portal_type):
    """Helper method to fix some vars after renaming a type in portal_types

    It will raise an IndexError if called with a nonexisting old_portal_type.
    If you like to swallow the error please use a try/except block in your own
    code and do NOT 'fix' this method.
    """
    at_tool = getToolByName(context, TOOL_NAME)
    __traceback_info__ = (context, old_portal_type, new_portal_type,
                          [t['portal_type'] for t in _types.values()])
    # Will fail if old portal type wasn't registered (DO 'FIX' THE INDEX ERROR!)
    old_type = [t for t in _types.values()
                if t['portal_type'] == old_portal_type][0]

    # Rename portal type
    old_type['portal_type'] = new_portal_type

    # Copy old templates to new portal name without references
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
        ctorName = 'manage_add%s' % typeName
        constructor = getattr(module, ctorName, None)
        if constructor is None:
            constructor = generateZMICtor(typeName, module)
        addFormName = 'manage_add%sForm' % typeName
        setattr(module, addFormName,
                BoundPageTemplateFile('base_add.pt', _zmi,
                                      __name__=addFormName,
                                      extra={'constructor':ctorName,
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))
        editFormName = 'manage_edit%sForm' % typeName
        setattr(klass, editFormName,
                BoundPageTemplateFile('base_edit.pt', _zmi,
                                      __name__=editFormName,
                                      extra={'handler':'processForm',
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))

        position = False
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
        icon = folderish and folder_icon or document_icon
        if klass.__dict__.has_key('content_icon'):
            icon = klass.content_icon
        elif hasattr(klass, 'factory_type_information'):
            factory_type_information = klass.factory_type_information
            if factory_type_information.has_key('content_icon'):
                icon = factory_type_information['content_icon']

        context.registerClass(
            t['klass'],
            constructors=(generatedForm, constructor),
            visibility=None,
            icon=icon
            )

def listTypes(package=None):
    values = _types.values()
    if package:
        values = [v for v in values if v['package'] == package]

    return values

def getType(name, package):
    key = '%s.%s' % (package, name)
    return _types[key]

class WidgetWrapper:
    """Wrapper used for drawing widgets without an instance.

    E.g.: for a search form.
    """
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
    """Archetypes tool, manage aspects of Archetype instances.
    """
    id = TOOL_NAME
    meta_type = TOOL_NAME.title().replace('_', ' ')

    implements(IArchetypeTool)

    isPrincipiaFolderish = True # Show up in the ZMI

    security = ClassSecurityInfo()

    meta_types = all_meta_types = ()

    manage_options = (
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

        ) + SQLStorageConfig.manage_options
        )

    security.declareProtected(permissions.ManagePortal,
                              'manage_uids')
    manage_uids = PageTemplateFile('viewContents', _www)
    security.declareProtected(permissions.ManagePortal,
                              'manage_templateForm')
    manage_templateForm = PageTemplateFile('manageTemplates',_www)
    security.declareProtected(permissions.ManagePortal,
                              'manage_debugForm')
    manage_debugForm = PageTemplateFile('generateDebug', _www)
    security.declareProtected(permissions.ManagePortal,
                              'manage_updateSchemaForm')
    manage_updateSchemaForm = PageTemplateFile('updateSchemaForm', _www)
    security.declareProtected(permissions.ManagePortal,
                              'manage_migrationForm')
    manage_migrationForm = PageTemplateFile('migrationForm', _www)
    security.declareProtected(permissions.ManagePortal,
                              'manage_dumpSchemaForm')
    manage_dumpSchemaForm = PageTemplateFile('schema', _www)
    security.declareProtected(permissions.ManagePortal,
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

    security.declareProtected(permissions.ManagePortal,
                              'manage_dumpSchema')
    def manage_dumpSchema(self, REQUEST=None):
        """XML Dump Schema of passed in class.
        """
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

    # Template Management
    # Views can be pretty generic by iterating the schema so we don't
    # register by type anymore, we just create per site selection
    # lists
    #
    # We keep two lists, all register templates and their
    # names/titles and the mapping of type to template bindings both
    # are persistent
    security.declareProtected(permissions.ManagePortal,
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


    security.declareProtected(permissions.View, 'lookupTemplates')
    def lookupTemplates(self, instance_or_portaltype=None):
        """Lookup templates by giving an instance or a portal_type.

        Returns a DisplayList.
        """
        results = []
        if not isinstance(instance_or_portaltype, basestring):
            portal_type = instance_or_portaltype.getTypeInfo().getId()
        else:
            portal_type = instance_or_portaltype
        try:
            templates = self._templates[portal_type]
        except KeyError:
            return DisplayList()
            # XXX Look this up in the types tool later
            # self._templates[instance] = ['base_view',]
            # templates = self._templates[instance]
        for t in templates:
            results.append((t, self._registeredTemplates[t]))

        return DisplayList(results).sortedByValue()

    security.declareProtected(permissions.View, 'listTemplates')
    def listTemplates(self):
        """Lists all the templates.
        """
        return DisplayList(self._registeredTemplates.items()).sortedByValue()

    security.declareProtected(permissions.ManagePortal, 'bindTemplate')
    def bindTemplate(self, portal_type, templateList):
        """Creates binding between a type and its associated views.
        """
        self._templates[portal_type] = templateList

    security.declareProtected(permissions.ManagePortal,
                              'manage_templates')
    def manage_templates(self, REQUEST=None):
        """Sets all the template/type mappings.
        """
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

        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_templateForm')

    security.declareProtected(permissions.View, 'typeImplementsInterfaces')
    def typeImplementsInterfaces(self, type, interfaces):
        """Checks if an type uses one of the given interfaces.
        """
        if isinstance(type, dict) and type.has_key('klass'):
            type = type['klass']
        for iface in interfaces:
            res = iface.implementedBy(type)
            if res:
                return True
        return False

    security.declareProtected(permissions.View, 'isTemplateEnabled')
    def isTemplateEnabled(self, type):
        """Checks if an type uses ITemplateMixin.
        """
        return self.typeImplementsInterfaces(type, [ITemplateMixin])

    security.declareProtected(permissions.View, 'listTemplateEnabledPortalTypes')
    def listTemplateEnabledPortalTypes(self):
        """Return a list of portal_types with ITemplateMixin
        """
        return self.listPortalTypesWithInterfaces([ITemplateMixin])

    security.declareProtected(permissions.View, 'listPortalTypesWithInterfaces')
    def listPortalTypesWithInterfaces(self, ifaces):
        """Returns a list of ftis of which the types implement one of
        the given interfaces.  Only returns AT types.

        Get a list of FTIs of types implementing IReferenceable:
        >>> tool = getToolByName(self.portal, TOOL_NAME)
        >>> meth = tool.listPortalTypesWithInterfaces
        >>> ftis = tool.listPortalTypesWithInterfaces([IReferenceable])

        Sort the type ids and print them:
        >>> type_ids = [fti.getId() for fti in ftis]
        >>> type_ids.sort()
        >>> type_ids
        ['ATBIFolder', 'ComplexType', ...]
        """
        pt = getToolByName(self, 'portal_types')
        value = []
        for data in listTypes():
            klass = data['klass']
            for iface in ifaces:
                if iface.implementedBy(klass):
                    ti = pt.getTypeInfo(data['portal_type'])
                    if ti is not None:
                        value.append(ti)
        return value

    # Type/Schema Management
    security.declareProtected(permissions.View, 'listRegisteredTypes')
    def listRegisteredTypes(self, inProject=False, portalTypes=False):
        """Return the list of sorted types.
        """

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
            ttool = getToolByName(self, 'portal_types')
            types = [ti.Metatype() for ti in ttool.listTypeInfo()]
	    if portalTypes:
                values = [v for v in values if v['portal_type'] in types]
            else:
                values = [v for v in values if v['meta_type'] in types]

        return values

    security.declareProtected(permissions.View, 'getTypeSpec')
    def getTypeSpec(self, package, type):
        t = self.lookupType(package, type)
        module = t['klass'].__module__
        klass = t['name']
        return '%s.%s' % (module, klass)

    security.declareProtected(permissions.View, 'listTypes')
    def listTypes(self, package=None, type=None):
        """Just the class.
        """
        if type is None:
            return [t['klass'] for t in listTypes(package)]
        else:
            return [getType(type, package)['klass']]

    security.declareProtected(permissions.View, 'lookupType')
    def lookupType(self, package, type):
        types = self.listRegisteredTypes()
        for t in types:
            if t['package'] != package:
                continue
            if t['meta_type'] == type:
                # We have to return the schema wrapped into the acquisition of
                # something to allow access. Otherwise we will end up with:
                # Your user account is defined outside the context of the object
                # being accessed.
                t['schema'] = ImplicitAcquisitionWrapper(t['schema'], self)
                return t
        return None

    security.declareProtected(permissions.ManagePortal,
                              'manage_installType')
    def manage_installType(self, typeName, package=None,
                           uninstall=None, REQUEST=None):
        """Un/Install a type TTW.
        """
        typesTool = getToolByName(self, 'portal_types')
        try:
            typesTool._delObject(typeName)
        except (ConflictError, KeyboardInterrupt):
            raise
        except: # XXX bare exception
            pass
        if uninstall is not None:
            if REQUEST:
                return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                                 '/manage_debugForm')
            return

        typeinfo_name = '%s: %s' % (package, typeName)

        # We want to run the process/modify_fti code which might not
        # have been called
        typeDesc = getType(typeName, package)
        process_types([typeDesc], package)
        klass = typeDesc['klass']

        # get the meta type of the FTI from the class, use the default FTI as default
        fti_meta_type = getattr(klass, '_at_fti_meta_type', None)
        if fti_meta_type in (None, 'simple item'):
            fti_meta_type = FactoryTypeInformation.meta_type

        typesTool.manage_addTypeInformation(fti_meta_type,
                                            id=typeName,
                                            typeinfo_name=typeinfo_name)
        t = getattr(typesTool, typeName, None)
        if t:
            t.title = getattr(klass, 'archetype_name',
                              typeDesc['portal_type'])

        # and update the actions as needed
        fixActionsForType(klass, typesTool)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                             '/manage_debugForm')

    security.declarePublic('getSearchWidgets')
    def getSearchWidgets(self, package=None, type=None,
                         context=None, nosort=None):
        """Empty widgets for searching.
        """
        return self.getWidgets(package=package, type=type,
                               context=context, mode='search', nosort=nosort)

    security.declarePublic('getWidgets')
    def getWidgets(self, instance=None,
                   package=None, type=None,
                   context=None, mode='edit',
                   fields=None, schemata=None, nosort=None):
        """Empty widgets for standalone rendering.
        """
        widgets = []
        w_keys = {}
        context = context is not None and context or self
        instances = instance is not None and [instance] or []
        f_names = fields
        if not instances:
            for t in self.listTypes(package, type):
                instance = t('fake_instance')
                instance._at_is_fake_instance = True
                wrapped = instance.__of__(context)
                wrapped.initializeArchetype()
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
                indexes=self.portal_catalog.indexes()
                fields = [f for f in fields
                          if (f.accessor and
                              not w_keys.has_key(f.accessor)
                              and f.accessor in indexes)]
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
                        field.vocabulary = DisplayList([('', _(u'at_search_any', default=u'<any>'))]) + \
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
        """Finds all object to check if they are 'referenceable'.
        """
        catalog = getToolByName(self, 'portal_catalog')
        brains = catalog(dict(id=[]))
        for b in brains:
            o = b.getObject()
            if o is not None:
                if IBaseObject.providedBy(o):
                    callback(o, *args, **kwargs)
            else:
                log('no object for brain: %s:%s' % (b,b.getURL()))


    security.declareProtected(permissions.View, 'enum')
    def enum(self, callback, *args, **kwargs):
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        for uid in keys:
            o = self.getObject(uid)
            if o:
                callback(o, *args, **kwargs)
            else:
                log('No object for %s' % uid)


    security.declareProtected(permissions.View, 'Content')
    def Content(self):
        """Return a list of all the content ids.
        """
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        results = catalog(dict(UID=keys))
        return results


    ## Management Forms
    security.declareProtected(permissions.ManagePortal,
                              'manage_doGenerate')
    def manage_doGenerate(self, sids=(), REQUEST=None):
        """(Re)generate types.
        """
        schemas = []
        for sid in sids:
            schemas.append(self.getSchema(sid))

        for s in schemas:
            s.generate()

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                             '/manage_workspace')

    security.declareProtected(permissions.ManagePortal,
                              'manage_inspect')
    def manage_inspect(self, UID, REQUEST=None):
        """Dump some things about an object hook in the debugger for now.
        """
        object = self.getObject(UID)
        log("uid: %s, schema: %s" % (object, object.Schema()))

        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         '/manage_uids')

    security.declareProtected(permissions.ManagePortal,
                              'manage_reindex')
    def manage_reindex(self, REQUEST=None):
        """Assign UIDs to all basecontent objects.
        """

        def _index(object, archetype_tool):
            archetype_tool.registerContent(object)

        self._rawEnum(_index, self)

        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         '/manage_uids')

    security.declareProtected(permissions.ManagePortal, 'index')
    index = manage_reindex

    def _listAllTypes(self):
        """List all types -- either currently known or known to us.
        """
        allTypes = _types.copy(); allTypes.update(self._types)
        return allTypes.keys()

    security.declareProtected(permissions.ManagePortal,
                              'getChangedSchema')
    def getChangedSchema(self):
        """Returns a list of tuples indicating which schema have changed.

        Tuples have the form (schema, changed).
        """
        list = []
        currentTypes = _types
        ourTypes = self._types
        modified = False
        keys = self._listAllTypes()
        keys.sort()
        for t in keys:
            if t not in ourTypes:
                # Add it
                ourTypes[t] = currentTypes[t]['signature']
                modified = True
                list.append((t, 0))
            elif t not in currentTypes:
                # Huh: what shall we do? We remove it -- this might be wrong!
                del ourTypes[t]
                modified = True
                # We do not add an entry because we cannot update
                # these objects (having no longer type information for them)
            else:
                list.append((t, ourTypes[t] != currentTypes[t]['signature']))
        if modified:
            self._p_changed = True
        return list


    security.declareProtected(permissions.ManagePortal,
                              'manage_updateSchema')
    def manage_updateSchema(self, REQUEST=None, update_all=None,
                            remove_instance_schemas=None):
        """Make sure all objects' schema are up to date.
        """
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
            remove_instance_schemas = REQUEST.form.get(
                'remove_instance_schemas', False)

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
            if remove_instance_schemas:
                func_update_changed = self._removeSchemaAndUpdateChangedObject
                func_update_all = self._removeSchemaAndUpdateObject
            else:
                func_update_changed = self._updateChangedObject
                func_update_all = self._updateObject
            if update_all:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=True, apply_func=func_update_all)
            else:
                catalog.ZopeFindAndApply(portal, obj_metatypes=meta_types,
                    search_sub=True, apply_func=func_update_changed)
            for t in update_types:
                self._types[t] = _types[t]['signature']
            self._p_changed = True

        print >> out, 'Done.'
        return out.getvalue()

    # A counter to ensure that in a given interval a subtransaction
    # commit is done.
    subtransactioncounter = 0

    def _updateObject(self, o, path, remove_instance_schemas=None):
        o._updateSchema(remove_instance_schemas=remove_instance_schemas)
        # Subtransactions to avoid eating up RAM when used inside a
        # 'ZopeFindAndApply' like in manage_updateSchema
        self.subtransactioncounter += 1
        # Only every 250 objects a sub-commit, otherwise it eats up all diskspace
        if not self.subtransactioncounter % 250:
            transaction.savepoint(optimistic=True)

    def _updateChangedObject(self, o, path):
        if not o._isSchemaCurrent():
            self._updateObject(o, path)

    def _removeSchemaAndUpdateObject(self, o, path):
        self._updateObject(o, path, remove_instance_schemas=True)

    def _removeSchemaAndUpdateChangedObject(self, o, path):
        if not o._isSchemaCurrent():
            self._removeSchemaAndUpdateObject(o, path)

    security.declareProtected(permissions.ManagePortal,
                              'manage_updateSchema')
    def manage_migrate(self, REQUEST=None):
        """Run Extensions.migrations.migrate.
        """
        from Products.Archetypes.Extensions.migrations import migrate
        out = migrate(self)
        self.manage_updateSchema()
        return out

    # Catalog management
    security.declareProtected(permissions.View,
                              'listCatalogs')
    def listCatalogs(self):
        """Show the catalog mapping.
        """
        return self.catalog_map

    security.declareProtected(permissions.ManagePortal,
                              'manage_updateCatalogs')
    def manage_updateCatalogs(self, REQUEST=None):
        """Set the catalog map for meta_type to include the list
        catalog_names.
        """
        prefix = 'catalog_names_'
        for key in REQUEST.form.keys():
            if key.startswith(prefix):
                k = key[len(prefix):]
                v = REQUEST.form.get(key)
                self.setCatalogsByType(k, v)

        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         '/manage_catalogs')

    security.declareProtected(permissions.ManagePortal,
                              'setCatalogsByType')
    def setCatalogsByType(self, portal_type, catalogList):
        """ associate catalogList with meta_type. (unfortunally not portal_type).

            catalogList is a list of strings with the ids of the catalogs.
            Each catalog is has to be a tool, means unique in site root.
        """
        self.catalog_map[portal_type] = catalogList


    security.declareProtected(permissions.View, 'getCatalogsByType')
    def getCatalogsByType(self, portal_type):
        """Return the catalog objects assoicated with a given type.
        """
        catalogs = []
        catalog_map = getattr(self, 'catalog_map', None)
        if catalog_map is not None:
            names = self.catalog_map.get(portal_type, ['portal_catalog'])
        else:
            names = ['portal_catalog']
        portal = getToolByName(self, 'portal_url').getPortalObject()
        for name in names:
            try:
                catalogs.append(getToolByName(portal, name))
            except (ConflictError, KeyboardInterrupt):
                raise
            except Exception, E:
                log('No tool %s' % name, E)
                pass
        return catalogs

    security.declareProtected(permissions.View, 'getCatalogsInSite')
    def getCatalogsInSite(self):
        """Return a list of ids for objects implementing ZCatalog.
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()
        res = []
        for object in portal.objectValues():
            if ICatalogTool.providedBy(object):
                res.append(object.getId())
                continue
            if IZCatalog.providedBy(object):
                res.append(object.getId())
                continue

        res.sort()

        return res

    security.declareProtected(permissions.View, 'visibleLookup')
    def visibleLookup(self, field, vis_key, vis_value='visible'):
        """Checks the value of a specific key in the field widget's
        'visible' dictionary.

        Returns True or False so it can be used within a lambda as
        the predicate for a filterFields call.
        """
        vis_dict = field.widget.visible
        value = ''
        if vis_dict.has_key(vis_key):
            value = field.widget.visible[vis_key]
        if value == vis_value:
            return True
        else:
            return False

    def has_graphviz(self):
        """Runtime check for graphviz, used in condition on tab.
        """
        return HAS_GRAPHVIZ

InitializeClass(ArchetypeTool)
