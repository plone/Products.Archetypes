import os
from types import ListType, TupleType
import Products.transform
from transform.interfaces import itransform, iengine, implements
from transform.data import datastream
from transform.chain import chain
from transform import transforms

from ExtensionClass import Base
from OFS.Folder import Folder
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import Persistent, InitializeClass
from ZODB.PersistentMapping import PersistentMapping

from Acquisition import Implicit, aq_parent
from OFS.SimpleItem import Item
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo

from Products.Archetypes.debug import log, log_exc

class TransformException(Exception) : pass

_www = os.path.join(os.path.dirname(__file__), 'www')

""" TODO:

  _ required transforms configuration (policy)
  _ user interface for chain construction
  _ use Schema for transform configuration ? that would be nice but may be a weird
    dependency...
  _ allow only one output type for transform ?
  _ make transforms thread safe
  _ make more transforms
  _ write doc about how to write a transformation
"""

def import_from_name(module_name):
    """ import and return a module by its name """
    __traceback_info__ = (module_name, )
    m = __import__(module_name)
    try:
        for sub in module_name.split('.')[1:]:
            m = getattr(m, sub)
    except AttributeError, e:
        raise ImportError(str(e))
    return m


class TransformTool(UniqueObject, ActionProviderBase, Folder):
    """ Transform tool, manage mime type oriented content transformation """

    id        = 'portal_transforms'
    meta_type = id.title().replace('_', ' ')
    isPrincipiaFolderish = 1 # Show up in the ZMI

    __implements__ = iengine

    meta_types = all_meta_types = (
        { 'name'   : 'Transform',
          'action' : 'manage_addTransformForm'},
        )

    manage_addTransformForm = PageTemplateFile('addTransform', _www)
    manage_reloadAllTransforms = PageTemplateFile('reloadAllTransforms', _www)

    manage_options = ((Folder.manage_options[0],) + Folder.manage_options[2:] +
                      (
        { 'label'   : 'Reload transforms',
          'action' : 'manage_reloadAllTransforms'},
        )
                      )

    security = ClassSecurityInfo()

    def __init__(self):
        self._mtmap    = PersistentMapping()

    def __call__(self, name, orig, data=None, **kwargs):
        """run a transform returning the raw data product"""
        data = self.convert(name, orig, data, **kwargs)
        return data.getData()

    def _wrap(self, name):
        """wrap a data object in an icache"""
        return datastream(name)

    def _unwrap(self, data):
        """ unwrap data from an icache """
        if implements(data, idatastream):
            data = data.getData()
        return data

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """ overload manage_afterAdd to finish initialization when the
        transform tool is added
        """
        Folder.manage_afterAdd(self, item, container)
        # first initialization
        transforms.initialize(self)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """ overload manage_renameObject to sync Transform's id and
        transform's name
        """
        Folder.manage_renameObject(self, id, new_id, REQUEST)
        tr = getattr(self, new_id)
        tr._transform.__name__ = new_id


    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addTransform')
    def manage_addTransform(self, id, module, REQUEST=None):
        """ add a new transform to the tool """
        transform = Transform(id, module)
        self._setObject(id, transform)
        self.registerTransform(id, transform)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


    security.declareProtected(CMFCorePermissions.ManagePortal, 'reloadTransforms')
    def reloadTransforms(self, ids=()):
        """ reload transforms with the given ids
        if no ids, reload all registered transforms

        return a list of (transform_id, transform_module) describing reloaded
        transforms
        """
        if not ids:
            ids = self.objectIds()
        reloaded = []
        for id in ids:
            o = getattr(self, id)
            o.reload()
            reloaded.append((id, o.module))
        return reloaded

    # mimetype oriented conversions ###########################################

    def registerTransform(self, name, transform):
        """ register a new transform """
        __traceback_info__ = (name, transform)
        if name not in self.objectIds():
            module = "%s" % transform.__module__
            transform = Transform(name, module)
            self._setObject(name, transform)
        self._mapTransform(transform)

    def unregisterTransform(self, name):
        """ unregister a known transform """
        self._unmapTransform(getattr(self, name))

    security.declarePublic('classify')
    def classify(self, data, mimetype=None, filename=None):
        """return a content type for this data or None
        None should rarely be returned as application/octet can be
        used to represent most types
        """
        registry = getToolByName(self, 'mimetypes_registry')
        return registry.classify(data,
                                 mimetype=mimetype,
                                 filename=filename)


    security.declarePublic('convertTo')
    def convertTo(self, target_mimetype, orig, data=None, **kwargs):
        """Convert orig to a given mimetype"""
        if not data:
            data = self._wrap(target_mimetype)

        orig_mt = self.classify(orig,
                                mimetype=kwargs.get('mimetype'),
                                filename=kwargs.get('filename'))

        registry = getToolByName(self, 'mimetypes_registry')
        target_mt = registry.lookup(target_mimetype)
        if target_mt:
            target_mt = target_mt[0]


        if not orig_mt or not target_mt:
            return None

        if orig_mt == target_mt: ## fastpath
            data.setData(orig)
            return data


        ## Only do single hop right now or None
        path = self._findPath(orig_mt, target_mt)
        log('PATH FROM %s TO %s : %s' % (orig_mt, target_mimetype, path))
        ## create a chain on the fly (sly)
        if not path:
            return None #XXX raise TransformError
        
        c = chain()
        for t in path:
            c.registerTransform(t.id, t._transform)

        if not data:
            data = self._wrap(target_mimetype)
        return c.convert(orig, data, **kwargs)


    security.declarePublic('convert')
    def convert(self, name, orig, data=None, **kwargs):
        """run a tranform of a given name on data returning the
        an idata entry with bound conditions"""
        if not data:
            data = self._wrap(name)

        transform = getattr(self, name)._transform
        data = transform.convert(orig, data, **kwargs)
        #bind in the mimetype as metadata
        md = data.getMetadata()
        md['mimetype'] = transform.outputs[0]

        return data

    def _mapTransform(self, transform):
        SEQ = (ListType, TupleType)
        registry = getToolByName(self, 'mimetypes_registry')
        for i in transform.inputs():
            mts = registry.lookup(i)
            if type(mts) not in SEQ:
                mts = (mts,)

            for mti in mts:
                mt_in = self._mtmap.setdefault(mti, PersistentMapping())
                for o in transform.outputs():
                    mtss = registry.lookup(o)
                    if type(mtss) not in SEQ:
                        mtss = (mtss,)
                    for mto in mtss:
                        mt_in.setdefault(mto, []).append(transform)

    def _unmapTransform(self, transform):
        SEQ = (ListType, TupleType)
        registry = getToolByName(self, 'mimetypes_registry')
        for i in transform.inputs():
            mts = registry.lookup(i)
            if type(mts) not in SEQ:
                mts = (mts,)

            for mti in mts:
                mt_in = self._mtmap.get(mti, {})
                for o in transform.outputs():
                    mtss = registry.lookup(o)
                    if type(mtss) not in SEQ:
                        mtss = (mtss,)
                    for mto in mtss:
                        l = mt_in[mto]
                        for i in range(len(l)):
                            if l.__name__ == l[i].__name__:
                                l.pop(i)
                                break
                        else:
                            log('Can\'t find transform %s' % transform.id)
    
    def _findPath(self, orig, target, required_transforms=()):
        #return a list of transforms
        path = []

        if not self._mtmap:
            return None

        registry = getToolByName(self, 'mimetypes_registry')

        # naive algorithm :
        #  find all possible paths with required transforms
        #  take the shortest
        #
        # it should be enough since we should not have so much possible paths
        shortest, winner = 9999, None
        for path in self._getPaths(registry.lookup(orig)[0],
                                  registry.lookup(target)[0],
                                  required_transforms):
            if len(path) < shortest:
                winner = path
                shortest = len(path)

        return winner

    def _getPaths(self, orig, target, requirements, path=None, result=None):
        if path is None:
            result = []
            path = []
            requirements = list(requirements)
        outputs = self._mtmap.get(orig)
        if outputs is None:
            return result
        path.append(None)
        for o_mt, transforms in outputs.items():
            for transform in transforms:
                required = 0
                if transform.id in requirements:
                    requirements.remove(transform.id)
                    required = 1
                if transform in path:
                    # avoid infinite loop...
                    continue
                path[-1] = transform
                if o_mt == target:
                    if not requirements:
                        result.append(path[:])
                else:
                    self._getPaths(o_mt, target, requirements, path, result)
                if required:
                    requirements.append(transform.id)
        path.pop()

        return result

InitializeClass(TransformTool)


class Transform(Implicit, Item, RoleManager, Persistent):
    """ a transform is an external method with
        additional configuration information
    """

    meta_type = 'Transform'

    meta_types = all_meta_types = ()

    manage_options = (
                      ({'label':'Configure',
                       'action':'manage_main'},
                       {'label':'Reload',
                       'action':'manage_reloadTransform'},) +
                      Item.manage_options
                      )

    manage_main = PageTemplateFile('configureTransform', _www)
    manage_reloadTransform = PageTemplateFile('reloadTransform', _www)

    security = ClassSecurityInfo()

    def __init__(self, id, module):
        self.id = id
        self.module = module
        self._config = PersistentMapping()
        self._tr_init(1)

    def __setstate__(self, state):
        """ __setstate__ is called whenever the instance is loaded
            from the ZODB, like when Zope is restarted.
            
            We should reload the wrapped transform at this time
        """
        Transform.inheritedAttribute('__setstate__')(self, state)
        self._tr_init()


    def _tr_init(self, set_conf=0):
        """ initialize the zope transform by loading the wrapped transform """
        __traceback_info__ = (self.module, )
        m = import_from_name(self.module)
        if not hasattr(m, 'register'):
            raise TransformException('Unvalid transform module %s: no register function defined' % module)

        transform = m.register()
        if not hasattr(transform, '__class__'):
            raise TransformException('Unvalid transform : transform is not a class')
        if not implements(transform, itransform):
            raise TransformException('Unvalid transform : itransform is not implemented by %s' % transform.__class__)
        
        transform.__name__ = self.id
        if set_conf and hasattr(transform, 'config'):
            self._config.update(transform.config)
        transform.config = self._config
        self._transform = transform
        return transform

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Item.manage_beforeDelete(self, item, container)
        if self is item:
            aq_parent(self).unregisterTransform(self.id)


    security.declarePublic('get_documentation')
    def get_documentation(self):
        """ return transform documentation """
        return self._transform.__doc__

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameters')
    def get_parameters(self):
        """ get transform's parameters names """
        return self._transform.config.keys()

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameter_value')
    def get_parameter_value(self, key):
        """ get value of a transform's parameter """
        return self._transform.config[key]

    security.declareProtected(CMFCorePermissions.ManagePortal, 'set_parameters')
    def set_parameters(self, REQUEST=None, **kwargs):
        """ set transform's parameters """
        if not kwargs:
            kwargs = REQUEST.form

        transform = self._transform
        for param, value in kwargs.items():
            if transform.config.has_key(param):
                transform.config[param] = value
            else:
                log('Warning: ignored parameter %s' % param)
                
        tr_tool = aq_parent(self)
        if kwargs.has_key('inputs') or kwargs.has_key('outputs'):
            # need to remap transform
            # FIXME: not sure map / unmap is a correct access point
            tr_tool._unmapTransform(transform)
            tr_tool._mapTransform(transform)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(tr_tool.absolute_url()+'/manage')

    security.declareProtected(CMFCorePermissions.ManagePortal, 'inputs')
    def inputs(self):
        """ return a list of input mime types """
        return self._transform.inputs

    security.declareProtected(CMFCorePermissions.ManagePortal, 'outputs')
    def outputs(self):
        """ return a list of output mime types """
        return self._transform.outputs

    security.declareProtected(CMFCorePermissions.ManagePortal, 'reload')
    def reload(self):
        """ reload the module where the transformation class is defined """
        log('Reloading transform %s' % self.module)
        m = import_from_name(self.module)
        reload(m)
        self._tr_init()


InitializeClass(Transform)


class TransformsChain(Implicit, Item, RoleManager, Persistent):
    """ a transforms chain is suite of transforms to apply in order.
    It follows the transform API so that a chain is itself a transform.
    """

    meta_type = 'TransformsChain'

    meta_types = all_meta_types = ()

    manage_options = (
                      ({'label':'Configure',
                       'action':'manage_main'},
                       {'label':'Reload',
                       'action':'manage_reloadTransform'},) +
                      Item.manage_options
                      )

    manage_main = PageTemplateFile('configureTransform', _www)
    manage_reloadTransform = PageTemplateFile('reloadTransform', _www)

    security = ClassSecurityInfo()

    def __init__(self, id, transform_ids):
        self.id = id
        self._tr_ids = transform_ids
        self._chain_init()

    def __setstate__(self, state):
        """ __setstate__ is called whenever the instance is loaded
            from the ZODB, like when Zope is restarted.
            
            We should rebuild the chain at this time
        """
        Transform.inheritedAttribute('__setstate__')(self, state)
        self._chain_init()


    def _chain_init(self):
        """ build the transforms chain """
        tr_tool = aq_parent(self)
        self._chain = c = chain()
        for id in self._tr_ids:
            transform = getattr(tr_tool, id)
            if transform.meta_type == 'Transform':
                c.registerTransform(transform.id, transform._transform)
            else:
                c.registerTransform(transform.id, transform._chain)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Item.manage_beforeDelete(self, item, container)
        if self is item:
            aq_parent(self).unregisterTransform(self.id)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameters')
    def get_parameters(self):
        """ get transform's parameters names """
        pass        

    security.declareProtected(CMFCorePermissions.ManagePortal, 'set_parameters')
    def set_parameters(self, REQUEST=None, **kwargs):
        """ set transform's parameters """
        pass
    
    security.declareProtected(CMFCorePermissions.ManagePortal, 'inputs')
    def inputs(self):
        """ return a list of input mime types """
        return self._chain.inputs

    security.declareProtected(CMFCorePermissions.ManagePortal, 'outputs')
    def outputs(self):
        """ return a list of output mime types """
        return self._chain.outputs

    security.declareProtected(CMFCorePermissions.ManagePortal, 'reload')
    def reload(self):
        """ reload the module where the transformation class is defined """
        tr_tool = aq_parent(self)
        for id in self._tr_ids:
            transform = getattr(tr_tool, id)
            transform.reload()

InitializeClass(TransformsChain)
