import os
from os.path import exists
from types import ListType, TupleType
try:
    from Products import transform
except ImportError:
    pass
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
from ZODB.PersistentList import PersistentList

from Acquisition import Implicit, aq_parent
from OFS.SimpleItem import Item
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo

from Products.Archetypes.debug import log, log_exc

class TransformException(Exception) : pass

_www = os.path.join(os.path.dirname(__file__), 'www')

""" TODO:

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
        { 'name'   : 'TransformsChain',
          'action' : 'manage_addTransformsChainForm'},
        )

    manage_addTransformForm = PageTemplateFile('addTransform', _www)
    manage_addTransformsChainForm = PageTemplateFile('addTransformsChain', _www)
    manage_editTransformationPolicyForm = PageTemplateFile('editTransformationPolicy', _www)
    manage_reloadAllTransforms = PageTemplateFile('reloadAllTransforms', _www)

    manage_options = ((Folder.manage_options[0],) + Folder.manage_options[2:] +
                      (
        { 'label'   : 'Policy',
          'action' : 'manage_editTransformationPolicyForm'},
        { 'label'   : 'Reload transforms',
          'action' : 'manage_reloadAllTransforms'},
        )
                      )

    security = ClassSecurityInfo()

    def __init__(self):
        self._mtmap = PersistentMapping()
        self._policies = PersistentMapping()

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
        try:
            # first initialization
            transforms.initialize(self)
        except:
            # may fail on copy
            pass

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """ overload manage_renameObject to sync Transform's id and
        transform's name
        """
        Folder.manage_renameObject(self, id, new_id, REQUEST)
        tr = getattr(self, new_id)
        tr.get_transform().__name__ = new_id

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addTransform')
    def manage_addTransform(self, id, module, REQUEST=None):
        """ add a new transform to the tool """
        transform = Transform(id, module)
        self._setObject(id, transform)
        self._mapTransform(transform)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addTransform')
    def manage_addTransformsChain(self, id, description, REQUEST=None):
        """ add a new transform to the tool """
        transform = TransformsChain(id, description)
        self._setObject(id, transform)
        self._mapTransform(transform)
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


    # Policy handling methods #################################################

    def manage_addPolicy(self, output_mimetype, required_transforms, REQUEST=None):
        """ add a policy for a given output mime types"""
        registry = getToolByName(self, 'mimetypes_registry')
        if not registry.lookup(output_mimetype):
            raise TransformException('Unknown MIME type')
        if self._policies.has_key(output_mimetype):
            msg = 'A policy for output %s is yet defined' % output_mimetype
            raise TransformException(msg)
        
        required_transforms = tuple(required_transforms)
        self._policies[output_mimetype] = required_transforms
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_editTransformationPolicyForm')

    def manage_delPolicies(self, outputs, REQUEST=None):
        """ remove policies for given output mime types"""
        for mimetype in outputs:
            del self._policies[mimetype]
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_editTransformationPolicyForm')
            
    def listPolicies(self):
        """ return the list of defined policies

        a policy is a 2-uple (output_mime_type, [list of required transforms])
        """
        # XXXFIXME: backward compat, should be removed latter
        if not hasattr(self, '_policies'):
            self._policies = PersistentMapping()
        return self._policies.items()

    
    # mimetype oriented conversions (iengine interface) ########################

    def registerTransform(self, name, transform):
        """register a new transform
        
        transform isn't a Zope Transform (the wrapper) but the wrapped transform
        the persistence wrapper will be created here
        """
        __traceback_info__ = (name, transform)
        # needed when call from transform.transforms.initialize which
        # register non zope transform
        module = "%s" % transform.__module__
        transform = Transform(name, module, transform)
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


        ## get a path to output mime type
        requirements = self._policies.get(target_mt, [])
        path = self._findPath(orig_mt, target_mt, list(requirements))        
        if not path and requirements:
            log('Unable to satisfy requirements %s' % ', '.join(requirements))
            path = self._findPath(orig_mt, target_mt)        
            
        if not path:
            log('NO PATH FROM %s TO %s : %s' % (orig_mt, target_mimetype, path))
            return None #XXX raise TransformError
        
        log('PATH FROM %s TO %s : %s' % (orig_mt, target_mimetype, path))
        ## create a chain on the fly (sly)
        c = chain()
        for t in path:
            c.registerTransform(t.id, t.get_transform())

        if not data:
            data = self._wrap(target_mimetype)
        return c.convert(orig, data, **kwargs)


    security.declarePublic('convert')
    def convert(self, name, orig, data=None, **kwargs):
        """run a tranform of a given name on data returning the
        an idata entry with bound conditions"""
        if not data:
            data = self._wrap(name)

        transform = getattr(self, name).get_transform()
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
                    for mto in mtss:
                        try:
                            if not transform in mt_in[mto]:
                                mt_in[mto].append(transform)
                        except KeyError:
                            mt_in[mto] = PersistentList([transform])

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
                    for mto in mtss:
                        l = mt_in[mto]
                        for i in range(len(l)):
                            if transform.id == l[i].id:
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


def make_config_persistent(kwargs):
    """ iterates on the given dictionnary and replace list by persistent list,
    dictionary by persistent mapping. 
    """
    for key, value in kwargs.items():
        if type(value) == type({}):
            p_value = PersistentMapping()
            p_value.update(value)
            kwargs[key] = p_value
        elif type(value) in (type(()), type([])):
            p_value = PersistentList()
            for i in value:
                p_value.append(i)
            kwargs[key] = p_value
    
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
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, id, module, transform=None):
        self.id = id
        self.module = module
        self._config = PersistentMapping()
        self._config.__allow_access_to_unprotected_subobjects__ = 1
        self._config_metadata = PersistentMapping()
        self._tr_init(1, transform)

    def __setstate__(self, state):
        """ __setstate__ is called whenever the instance is loaded
            from the ZODB, like when Zope is restarted.
            
            We should reload the wrapped transform at this time
        """
        Transform.inheritedAttribute('__setstate__')(self, state)
        self._tr_init()


    def _tr_init(self, set_conf=0, transform=None):
        """ initialize the zope transform by loading the wrapped transform """
        __traceback_info__ = (self.module, )
        if transform is None:
            m = import_from_name(self.module)
            reload(m)
            if not hasattr(m, 'register'):
                msg = 'Unvalid transform module %s: no register function defined' % module
                raise TransformException(msg)
            transform = m.register()
            
        if not hasattr(transform, '__class__'):
            raise TransformException('Unvalid transform : transform is not a class')
        if not implements(transform, itransform):
            raise TransformException('Unvalid transform : itransform is not implemented by %s' % transform.__class__)
        
        transform.__name__ = self.id
        if set_conf and hasattr(transform, 'config'):
            self._config.update(transform.config)
            make_config_persistent(self._config)
            if hasattr(transform, 'config_metadata'):
                self._config_metadata.update(transform.config_metadata)
                make_config_persistent(self._config_metadata)
                
        transform.config = self._config
        transform.config_metadata = self._config_metadata
        self._transform = transform
        return transform

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Item.manage_beforeDelete(self, item, container)
        if self is item:
            aq_parent(self).unregisterTransform(self.id)


    security.declarePublic('get_transform')
    def get_transform(self):
        """ return the actual transform """
        return self._transform
    
    security.declarePublic('get_documentation')
    def get_documentation(self):
        """ return transform documentation """
        return self._transform.__doc__

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameters')
    def get_parameters(self):
        """ get transform's parameters names """
        keys = self._transform.config.keys()
        keys.sort()
        return keys

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameter_value')
    def get_parameter_value(self, key):
        """ get value of a transform's parameter """
        value = self._config[key]
        type = self.get_parameter_infos(key)[0]
        # FIXME: this is done to allow access to PersistentMapping and
        #        PersistentList in templates
        #        there must be another way to do that
        # OTH, it avoid external modification of dict and list 
        if type == 'dict':
            result = {}
            for key, val in value.items():
                result[key] = val
        elif type == 'list':
            result = list(value)
        else:
            result = value
        return result

    security.declareProtected(CMFCorePermissions.ManagePortal, 'get_parameter_infos')
    def get_parameter_infos(self, key):
        """ get informations about a parameter

        return a tuple (type, label, description [, type specific data])
        where type in (string, int, list, dict)
              label and description are two string describing the field
        there may be some additional elements specific to the type :
             (key label, value label) for the dict type
        """
        try:
            return tuple(self._config_metadata[key])
        except KeyError:
            return 'string', '', ''
        
    security.declareProtected(CMFCorePermissions.ManagePortal, 'set_parameters')
    def set_parameters(self, REQUEST=None, **kwargs):
        """ set transform's parameters """
        if not kwargs:
            kwargs = REQUEST.form
        self.preprocess_param(kwargs)
        for param, value in kwargs.items():
            try:
                self.get_parameter_value(param)
            except KeyError:
                log('Warning: ignored parameter %s' % param)
                continue
            meta = self.get_parameter_infos(param)
            self._config[param] = VALIDATORS[meta[0]](value)
                
        tr_tool = aq_parent(self)
        # need to remap transform if necessary
        if kwargs.has_key('inputs') or kwargs.has_key('outputs'):
            # FIXME: not sure map / unmap is a correct access point
            tr_tool._unmapTransform(self)
            tr_tool._mapTransform(self)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(tr_tool.absolute_url()+'/manage_main')

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
        self._tr_init()

    def preprocess_param(self, kwargs):
        """ preprocess param fetched from an http post to handle optional dictionary
        """
        for param in self.get_parameters():
            if self.get_parameter_infos(param)[0] == 'dict':
                try:
                    keys = kwargs[param + '_key']
                    del kwargs[param + '_key']
                except:
                    keys = ()
                try:
                    values = kwargs[param + '_value']
                    del kwargs[param + '_value']
                except:
                    values = ()
                kwargs[param] = dict = {}
                for key, value in zip(keys, values):
                    key = key.strip()
                    if key:
                        value = value.strip()
                        if exists(value):
                            dict[key] = value

InitializeClass(Transform)

    
VALIDATORS = {
    'int' : int,
    'string' : str,
    'list' : PersistentList,
    'dict' : PersistentMapping,
    }

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

    manage_main = PageTemplateFile('editTransformsChain', _www)
    manage_reloadTransform = PageTemplateFile('reloadTransform', _www)

    security = ClassSecurityInfo()

    def __init__(self, id, description, ids=()):
        self.id = id
        self.description = description
        self._object_ids = list(ids)
        self._chain_init()

    def __setstate__(self, state):
        """ __setstate__ is called whenever the instance is loaded
            from the ZODB, like when Zope is restarted.
            
            We should rebuild the chain at this time
        """
        TransformsChain.inheritedAttribute('__setstate__')(self, state)
        self._chain = None

    def _chain_init(self):
        """ build the transforms chain """
        tr_tool = getToolByName(self, 'portal_transforms')
        self._chain = c = chain()
        for id in self._object_ids:
            object = getattr(tr_tool, id)
            c.registerTransform(object.id, object.get_transform())

    security.declarePublic('get_transform')
    def get_transform(self):
        """ return the actual transform """
        if self._chain is None:
            self._chain_init()
        return self._chain
    
    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Item.manage_beforeDelete(self, item, container)
        if self is item:
            aq_parent(self).unregisterTransform(self.id)
            
    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addTransform')
    def manage_addObject(self, id, REQUEST=None):
        """ add a new transform or chain to the chain """
        assert id not in self._object_ids
        self._object_ids.append(id)
        self._chain_init()
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_delObjects')
    def manage_delObjects(self, ids, REQUEST=None):
        """ delete the selected mime types """
        for id in ids:
            self._object_ids.remove(id)
        self._chain_init()
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


    # transforms order handling ###############################################

    security.declareProtected(CMFCorePermissions.ManagePortal, 'move_object_to_position')
    def move_object_to_position(self, id, newpos):
        """ overriden from OrderedFolder to store id instead of objects
        """
        oldpos = self._object_ids.index(id)
        if (newpos < 0 or newpos == oldpos or newpos >= len(self._object_ids)):
            return 0
        self._object_ids.pop(oldpos)
        self._object_ids.insert(newpos, id)
        self._chain_init()
        return 1

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_up')
    def move_object_up(self, id, REQUEST=None):
        """  move object with the given id up in the list """
        newpos = self._object_ids.index(id) - 1
        self.move_object_to_position(id, newpos)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_down')
    def move_object_down(self, id, REQUEST=None):
        """  move object with the given id down in the list """
        newpos = self._object_ids.index(id) + 1
        self.move_object_to_position(id, newpos)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')


    # Z transform interface ###################################################    

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
        for tr in self.objectValues():
            tr.reload()


    # utilities ###############################################################

    security.declareProtected(CMFCorePermissions.ManagePortal, 'listAddableObjects')
    def listAddableObjectIds(self):
        """ return a list of addable transform """
        tr_tool = aq_parent(self)
        return [id for id in tr_tool.objectIds() if not id in self._object_ids]
        
    security.declareProtected(CMFCorePermissions.ManagePortal, 'listAddableObjects')
    def objectIds(self):
        """ return a list of addable transform """
        return tuple(self._object_ids)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'listAddableObjects')
    def objectValues(self):
        """ return a list of addable transform """
        tr_tool = aq_parent(self)
        return [getattr(tr_tool, id) for id in self.objectIds()]

InitializeClass(TransformsChain)
