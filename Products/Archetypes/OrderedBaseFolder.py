"""
OrderedBaseFolder derived from OrderedFolder by Stephan Richter, iuveno AG.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore import CMFCorePermissions
from Products.CMFDefault.SkinnedFolder import SkinnedFolder

from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from BaseObject import BaseObject
from CatalogMultiplex  import CatalogMultiplex
from debug import log, log_exc
from interfaces.base import IBaseFolder
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata
from interfaces.orderedfolder import IOrderedFolder

class OrderedFolder( SkinnedFolder ):

    __implements__ = IOrderedFolder

    security = ClassSecurityInfo()

    security.declareProtected(CMFCorePermissions.ManageProperties, 'get_object_position')
    def get_object_position(self, id):
        i = 0
        for obj in self._objects:
            if obj['id'] == id:
                return i
            i = i+1
        # If the object was not found, throw an error.
        raise 'ObjectNotFound', 'The object with the id "%s" does not exist.' % id

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_to_position')
    def move_object_to_position(self, id, newpos):
        oldpos = self.get_object_position(id)
        if (newpos < 0 or newpos == oldpos or newpos >= len(self._objects)):
            return 0
        obj = self._objects[oldpos]
        objects = list(self._objects)
        del objects[oldpos]
        objects.insert(newpos, obj)
        self._objects = tuple(objects)
        return 1

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_up')
    def move_object_up(self, id):
        newpos = self.get_object_position(id) - 1
        return self.move_object_to_position(id, newpos)

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_down')
    def move_object_down(self, id):
        newpos = self.get_object_position(id) + 1
        return self.move_object_to_position(id, newpos)

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_to_top')
    def move_object_to_top(self, id):
        newpos = 0
        return self.move_object_to_position(id, newpos)

    security.declareProtected(CMFCorePermissions.ManageProperties, 'move_object_to_bottom')
    def move_object_to_bottom(self, id):
        newpos = len(self._objects) - 1
        return self.move_object_to_position(id, newpos)

    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename a particular sub-object"""
        # Since OFS.CopySupport.CopyContainer::manage_renameObject uses
        #_setObject manually, we have to take care of the order after it is done.
        oldpos = self.get_object_position(id)
        res = SkinnedFolder.manage_renameObject(self, id, new_id, REQUEST)
        self.move_object_to_position(new_id, oldpos)
        return res

    def _setObject(self, id, object, roles=None, user=None, set_owner=1, position=None):
        res = SkinnedFolder._setObject(self, id, object, roles, user, set_owner)
        if position is not None:
            self.move_object_to_position(id, position)
        # otherwise it was inserted at the end
        return res

InitializeClass(OrderedFolder)

class OrderedBaseFolder(BaseObject,
                        Referenceable,
                        CatalogMultiplex,
                        OrderedFolder,
                        ExtensibleMetadata):
    """ An ordered base Folder implementation """

    __implements__ = (IBaseFolder, IReferenceable,
                      IExtensibleMetadata,
                      IOrderedFolder)

    manage_options = SkinnedFolder.manage_options
    content_icon = "folder_icon.gif"

    schema = BaseObject.schema + ExtensibleMetadata.schema

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        OrderedFolder.__init__(self, oid, self.Title())
        BaseObject.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)
        BaseObject.manage_afterAdd(self, item, container)
        OrderedFolder.manage_afterAdd(self, item, container)
        CatalogMultiplex.manage_afterAdd(self, item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)
        OrderedFolder.manage_afterClone(self, item)
        CatalogMultiplex.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)
        OrderedFolder.manage_beforeDelete(self, item, container)
        CatalogMultiplex.manage_beforeDelete(self, item, container)

InitializeClass(OrderedBaseFolder)
