from __future__ import nested_scopes

import os.path
import sys
import time
import random
from copy import deepcopy
from types import StringType
from md5 import md5
from DateTime import DateTime

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.PersistentMapping import PersistentMapping

from interfaces.base import IBaseObject, IBaseFolder
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata

from ClassGen import generateClass
from ReferenceEngine import ReferenceEngine
from SQLStorageConfig import SQLStorageConfig
from config  import PKG_NAME, TOOL_NAME, UID_CATALOG
from debug import log, log_exc
from utils import capitalize, findDict, DisplayList, unique
from Renderer import renderer

_www = os.path.join(os.path.dirname(__file__), 'www')

# This is the template that we produce our custom types from
# Never actually used
base_factory_type_information = (
    { 'id': 'Archetype'
      ,  'content_icon': 'document_icon.gif'
      , 'meta_type': 'Archetype'
      , 'description': ( 'Archetype for flexible types')
      , 'product': 'Unknown Package'
      , 'factory': 'addContent'
      , 'immediate_view': 'portal_form/base_edit'
      , 'global_allow': 1
      , 'filter_content_types': 0
      , 'actions': (
                     { 'id': 'view',
                       'name': 'View',
                       'action': 'base_view',
                       'permissions': (CMFCorePermissions.View,),
                       },

                     { 'id': 'edit',
                       'name': 'Edit',
                       'action': 'portal_form/base_edit',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'metadata',
                       'name': 'Properties',
                       'action': 'portal_form/base_metadata',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'references',
                       'name': 'References',
                       'action': 'portal_form/reference_edit',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     )
      }, )


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

    if not IReferenceable.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'references')
        refs['visible'] = 0

    if not IExtensibleMetadata.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'metadata')
        refs['visible'] = 0


def generateCtor(type, module):
    name = capitalize(type)
    ctor = """
def add%s(self, id, **kwargs):
    o = %s(id)
    self._setObject(id, o)
    o = getattr(self, id)
    o.initializeArchetype(**kwargs)
    return id
""" % (name, type)

    exec ctor in module.__dict__
    return getattr(module, "add%s" % name)


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
        'package' : package,
        'module' : sys.modules[klass.__module__],
        'schema' : klass.schema,
        'signature' : klass.schema.signature(),
        # backward compatibility, remove later
        'type' : klass.schema,
        }

    _types[klass.meta_type] = data
    for tc in _types_callback:
        tc(klass, package)


def listTypes(package=None):
    values = _types.values()
    if package:
        values = [v for v in values if v['package'] == package]

    return values

def getType(name):
    return _types[name]

class TTWSchema(SimpleItem):
    def __init__(self, oid, text=None):
        self.id = oid
        self.text = text
        if text:
            self.compileSchema(text)


    def compileSchema(self, text):
        """Take the text of a schema and produce a field list
        by evaling in a preped namespace"""
        ns = {}
        # We need to import these here to avoid circular imports
        import BaseContent
        import ExtensibleMetadata

        exec "from Products.Archetypes.public import *" in ns

        exec text in ns
        schema = ns['schema']
        schema = BaseContent.BaseContent.Schema() + \
                 ExtensibleMetadata.ExtensibleMetadata.Schema() + schema
        self.schema = schema

    def register(self, typesTool):
        #update reg with types tool
        #update actions
        #changes to schema might need classgen changes
        try:
            typesTool._delObject(self.id)
        except:
            pass

        typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                            id=self.id,
                                            typeinfo_name="%s: %s" % (PKG_NAME, "TTW" ))
        t = getattr(typesTool, self.id, None)
        if t:
            process_types((t,), PKG_NAME)


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
                    SQLStorageConfig, Folder, ReferenceEngine):
    """ Archetypes tool, manage aspects of Archetype instances """
    id        = TOOL_NAME
    meta_type = TOOL_NAME.title().replace('_', ' ')
    isPrincipiaFolderish = 1 # Show up in the ZMI

    security = ClassSecurityInfo()

    meta_types = all_meta_types = ((
        { 'name'   : 'Schema',
          'action' : 'manage_addSchemaForm'},
        ))

    manage_options=(
        (Folder.manage_options[0],) +
        (
        { 'label'  : 'Templates',
          'action' : 'manage_templateForm',
          },

        { 'label'  : 'Introspect',
          'action' : 'manage_debugForm',
          },

        { 'label'  : 'Update Schema',
          'action' : 'manage_updateSchemaForm',
          },

        {  'label'  : 'UIDs',
           'action' : 'manage_uids',
           },

        {  'label'  : 'Catalogs',
           'action' : 'manage_catalogs',
           },

        )  + SQLStorageConfig.manage_options
        )

    manage_uids = PageTemplateFile('viewContents', _www)
    manage_addSchemaForm = PageTemplateFile('addSchema', _www)
    manage_templateForm = PageTemplateFile('manageTemplates',_www)
    manage_debugForm = PageTemplateFile('generateDebug', _www)
    manage_updateSchemaForm = PageTemplateFile('updateSchemaForm', _www)
    manage_dumpSchemaForm = PageTemplateFile('schema', _www)
    manage_catalogs = PageTemplateFile('manage_catalogs', _www)



    def __init__(self):
        ReferenceEngine.__init__(self)
        self._schemas = PersistentMapping()
        self._templates = PersistentMapping()
        self.catalog_map = PersistentMapping() # meta_type -> [names of CatalogTools]

        self._types = {}

        for t in _types.values():
            self._types[t['klass'].meta_type] = \
                {'signature':t['signature'], 'update':1}
        _types_callback.append(lambda klass, package:self.registerType(klass, package))
        self.last_types_update = DateTime()


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
    def registerTemplate(self, template, name, portal_type=None):
        # types -> { set of template names }
        if type(portal_type) not in  [type(()), type([])]:
            portal_type = (portal_type,)

        for p in portal_type:
            self._templates.setdefault(p,
                                       PersistentMapping())[template] = name

    def lookupTemplates(self, instance=None):
        results = []
        if type(instance) is not StringType:
            instance = instance.portal_type

        results += self._templates.get(instance, {}).items()
        results += self._templates.get(None, {}).items()
        return DisplayList(results).sortedByValue()

    def listTemplates(self):
        """list all the templates"""
        results = []
        for d in self._templates.values():
            for p in d.items():
                results.append(p)
        results = unique(results)
        return DisplayList(results).sortedByValue()

    def listCatalogs(self):
        """show the catalog mapping"""
        return self.catalog_map



    ## Type/Schema Management
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


    def getTypeSpec(self, package, type):
        t = self.lookupType(package, type)
        module = t['klass'].__module__
        klass = t['name']
        return '%s.%s' % (module, klass)

    def listTypes(self, package=None):
        """just the class"""
        return [t['klass'] for t in listTypes(package)]


    def lookupType(self, package, type):
        types = self.listRegisteredTypes()
        for t in types:
            if t['package'] != package: continue
            if t['name'] == type:
                return t
        return None

    def getSchema(self, sid):
        return self._schemas[sid]

    def getSearchWidgets(self, package=None):
        """empty widgets for searching"""

        # possible problem: assumes fields with same name can be
        # searched with the same widget
        widgets = {}
        for t in self.listTypes(package):
            instance = t('fake')
            from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
            DefaultDublinCoreImpl.__init__(instance)
            instance._is_fake_instance = 1
            instance.schema = instance.schema.copy()
            instance = instance.__of__(self)
            for field in instance.schema.fields():
                if field.index and not widgets.has_key(field.getName()):
                    field.required = 0
                    field.addable = 0 # for ReferenceField
                    if not isinstance(field.vocabulary, DisplayList):
                        field.vocabulary = field.Vocabulary(instance)
                    if '' not in field.vocabulary.keys():
                        field.vocabulary = DisplayList([('', '<any>')]) + \
                                           field.vocabulary
                        field.default = ''
                    widgets[field.getName()] = WidgetWrapper(field_name=field.getName(),
                                                        mode='search',
                                                        widget=field.widget,
                                                        instance=instance,
                                                        field=field,
                                                        accessor=field.getDefault)
        widgets = widgets.items()
        widgets.sort()
        return [widget for name, widget in widgets]

    ## Reference Engine Support
    def lookupObject(self, uid):
        if not uid:
            return None
        object = None
        catalog = getToolByName(self, UID_CATALOG)
        result  = catalog({'UID' : uid})
        if result:
            #This is an awful workaround for the UID under containment
            #problem. NonRefs will aq there parents UID which is so
            #awful I am having trouble putting it into words.
            for object in result:
                o = object.getObject()
                if o is not None:
                    if IReferenceable.isImplementedBy(o):
                        return o
        return None

    def getObject(self, uid):
        return self.lookupObject(uid)


    def reference_url(self, object):
        """Return a link to the object by reference"""
        uid = object.UID()
        return "%s/lookupObject?uid=%s" % (self.absolute_url(), uid)


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


    def enum(self, callback, *args, **kwargs):
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        for uid in keys:
            o = self.getObject(uid)
            if o:
                callback(o, *args, **kwargs)
            else:
                log("no object for %s" % uid)

    def _genId(self, object):
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')

        cid = object.getId()
        i = 0
        counter = 0
        postfix = ''
        while cid in keys:
            if counter > 0:
                g = random.Random(time.time())
                postfix = g.random() * 10000
            cid = "%s-%s%s" % (object.getId(),
                               i, postfix)
            i = int((time.time() % 1.0) * 10000)
            counter += 1

        return cid

    def registerContent(self, object):
        """register a content object and set its unique id"""
        cid = self.getUidFrom(object)
        if cid is None:
            cid = self._genId(object)
            self.setUidOn(object, cid)

        return cid

    def unregisterContent(self, object):
        """remove all refs/backrefs from an object"""
        cid = self.getUidFrom(object)
        self._delReferences(cid)
        return cid


    def getUidFrom(self, object):
        """return the UID for an object or None"""
        value = None

        if hasattr(object, "_getUID"):
            value = object._getUID()

        return value

    def setUidOn(self, object, cid):
        if hasattr(object, "_setUID"):
            object._setUID(cid)


    def Content(self):
        """Return a list of all the content ids"""
        catalog = getToolByName(self, UID_CATALOG)
        keys = catalog.uniqueValuesFor('UID')
        results = catalog(UID=keys)
        return results


    ## Management Forms
    def manage_addSchema(self, id, schema, REQUEST=None):
        """add a schema to the generator tool"""
        schema = schema.replace('\r', '')

        if not self._schemas.has_key(id):
            s = TTWSchema(id, schema)
            self._schemas[id] = s
            portal_types = getToolByName(self, 'portal_types')
            s.register(portal_types)

        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/manage_workspace")

    def manage_templates(self, submit, REQUEST=None):
        """template mgmt method"""
        if submit == "Add Template":
            name = REQUEST.form.get('name')
            vis = REQUEST.form.get('vis')
            types = REQUEST.form.get('types')

            if name and vis:
                self.registerTemplate(name, vis, types)

        if submit == "Unregister":
            list = REQUEST.form.get('template')
            clean = []
            for d in self._templates.values():
                for k, v in d.items():
                    if k in list:
                        clean.append((d, k))

            for d, k in clean:
                del d[k]


        if REQUEST:
            return REQUEST.RESPONSE.redirect(self.absolute_url() + \
                                             "/manage_templateForm")


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

    def manage_inspect(self, UID, REQUEST=None):
        """dump some things about an object hook in the debugger for
        now"""
        object = self.getObject(UID)
        #if object:
        #    import pdb;pdb.set_trace()
        log(object, object.Schema(), dir(object))


        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         "/manage_uids"
                                         )

    def manage_reindex(self, REQUEST=None):
        """assign UIDs to all basecontent objects"""

        def _index(object, archetype_tool):
                archetype_tool.registerContent(object)

        self._rawEnum(_index, self)

        return REQUEST.RESPONSE.redirect(self.absolute_url() +
                                         "/manage_uids"
                                         )


    index = manage_reindex


    def getChangedSchema(self):
        """Get a list of schema that have changed"""
        list = []
        for t in self._types.keys():
            if self._types[t]['update']:
                list.append(t)
        return list


    security.declareProtected('Manage portal', 'manage_updateSchema')
    def manage_updateSchema(self):
        """Make sure all objects' schema are up to date"""
        from StringIO import StringIO
        out = StringIO()
        print >> out, 'Updating schema...'

        for t in self._types.keys():
            if not self._types[t]['update']:
                continue
            catalog = getToolByName(self, UID_CATALOG)
            result = catalog._catalog.searchResults({'meta_type' : t})

            classes = {}
            for r in result:
                try:
                    o = r.getObject()
                    if hasattr(o, '_updateSchema'):
                        if not o._isSchemaCurrent():
                            o._updateSchema(out=out)
                except KeyError:
                    pass
            self._types[t]['update'] = 0
            self._p_changed = 1
        return out.getvalue()


    def __setstate__(self, v):
        """Add a callback to track product registrations"""
        ArchetypeTool.inheritedAttribute('__setstate__')(self, v)
        global _types
        global _types_callback
        import sys
        if hasattr(self, '_types'):
            if not hasattr(self, 'last_types_update') or self.last_types_update.lessThan(last_load):
                for t in _types.values():
#                    if t['klass'].meta_type == 'Survey':
#                        import pdb
#                        pdb.set_trace()
                    meta_type = t['klass'].meta_type
                    if self._types.has_key(meta_type):
                        update = (t['signature'] != self._types[meta_type]['signature'])
                    else:
                        update = 1
                    self._types[meta_type] = {'signature':t['signature'], 'update':update}
                _types_callback.append(lambda klass, package:self.registerType(klass, package))
                self.last_types_update = DateTime()


    def registerType(self, klass, package):
        """This gets called every time registerType is called as soon as the
        hook is installed by setstate"""
        # See if the schema has changed.  If it has, flag it
        update = 0
        sig = klass.schema.signature()
        old_data = self._types.get(klass.meta_type, None)
        if old_data:
            update = old_data.get('update', 0)
            old_sig = old_data.get('signature', None)
            if sig != old_sig:
                update = 1
        self._types[klass.meta_type] = {'signature':sig, 'update':update}
        self._p_changed = 1



    def manage_updateCatalogs(self, REQUEST=None):
        """set the catalog map for meta_type to include the list catalog_names"""
        prefix = 'catalog_names_'
        for key in REQUEST.form.keys():
            if key.startswith(prefix):
                k = key[len(prefix):]
                v = REQUEST.form.get(key)
                if type(v) in (type(''), type(u'')):
                    v = v.split('\n')
                v = [i.strip() for i in v if i.strip()]
                self.catalog_map[k] = v

        return REQUEST.RESPONSE.redirect(self.absolute_url() + "/manage_catalogs")

    def getCatalogsByType(self, meta_type):
        """Return the catalog objects assoicated with a given type"""
        catalogs = []
        names = self.catalog_map.get(meta_type, ['portal_catalog', UID_CATALOG])
        for name in names:
            try:
                catalogs.append(getToolByName(self, name))
            except Exception, E:
                log("No tool", name, E)
                pass
        return catalogs



InitializeClass(ArchetypeTool)
