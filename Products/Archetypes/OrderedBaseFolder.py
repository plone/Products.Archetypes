"""
OrderedBaseFolder derived from OrderedFolder by Stephan Richter, iuveno AG.
OrderedFolder adapted to Zope 2.7 style interface by Jens.KLEIN@jensquadrat.de

$Id: OrderedBaseFolder.py,v 1.4 2003/11/17 10:10:29 yenzenz Exp $
"""

from AccessControl import ClassSecurityInfo, Permissions
from Globals import InitializeClass
from Products.CMFCore.CMFCorePermissions import AddPortalFolders, \
     AddPortalContent, ModifyPortalContent, ManageProperties
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.SkinnedFolder import SkinnedFolder

from Referenceable import Referenceable
from ExtensibleMetadata import ExtensibleMetadata
from BaseObject import BaseObject
from BaseFolder import BaseFolder
from debug import log, log_exc
from interfaces.base import IBaseFolder
from interfaces.referenceable import IReferenceable
from interfaces.metadata import IExtensibleMetadata
from interfaces.orderedfolder import IOrderedFolder
from types import StringType

from config import USE_OLD_ORDEREDFOLDER_IMPLEMENTATION

# this import can change with Zope 2.7 to
try:
    from OFS.IOrderSupport import IOrderedContainer as IZopeOrderedContainer
    hasZopeOrderedSupport=1
except ImportError:
    hasZopeOrderedSupport=0
# atm its safer defining an own so we need an ugly hack to make Archetypes 
# OrderedBaseFolder work with Plone 2.0 
try:
    from Products.CMFPlone.interfaces.OrderedContainer import IOrderedContainer
except:
    from interfaces.orderedfolder import IOrderedContainer

# implement this class only in backward compatibility mode
class OrderedFolder( SkinnedFolder ):
    """ DEPRECATED, may be removed in next releaeses """

    __implements__ = IOrderedFolder

    security = ClassSecurityInfo()

    security.declareProtected(ManageProperties, 'get_object_position')
    def get_object_position(self, id):
        i = 0
        for obj in self._objects:
            if obj['id'] == id:
                return i
            i = i+1
        # If the object was not found, throw an error.
        raise 'ObjectNotFound', 'The object with the id "%s" does not exist.' % id

    security.declareProtected(ManageProperties, 'move_object_to_position')
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

    security.declareProtected(ManageProperties, 'move_object_up')
    def move_object_up(self, id):
        newpos = self.get_object_position(id) - 1
        return self.move_object_to_position(id, newpos)

    security.declareProtected(ManageProperties, 'move_object_down')
    def move_object_down(self, id):
        newpos = self.get_object_position(id) + 1
        return self.move_object_to_position(id, newpos)

    security.declareProtected(ManageProperties, 'move_object_to_top')
    def move_object_to_top(self, id):
        newpos = 0
        return self.move_object_to_position(id, newpos)

    security.declareProtected(ManageProperties, 'move_object_to_bottom')
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

class OrderedContainer:

    if hasZopeOrderedSupport:
        # got the IOrderedContainer interface from zope 2.7, too
        # make shure this implementation fullfilles both interfaces
        __implements__  = (IOrderedContainer, IZopeOrderedContainer)
    else:
        __implements__  = (IOrderedContainer,)

    security = ClassSecurityInfo()

    security.declareProtected(ModifyPortalContent, 'moveObject')
    def moveObject(self, id, position):
        obj_idx  = self.getObjectPosition(id)
        if obj_idx == position:
            return None
        elif position < 0:
            position = 0

        metadata = list(self._objects)
        obj_meta = metadata.pop(obj_idx)
        metadata.insert(position, obj_meta)
        self._objects = tuple(metadata)

    # here the implementing of IOrderedContainer starts
    # if plone sometime depends on zope 2.7 it should be replaced by mixing in
    # the 2.7 specific class OSF.OrderedContainer.OrderedContainer

    security.declareProtected(ModifyPortalContent, 'moveObjectsByDelta')
    def moveObjectsByDelta(self, ids, delta):
        """ Move specified sub-objects by delta.
        """
        if type(ids) is StringType:
            ids = (ids,)
        min_position = 0
        #objects = list(self._objects)
        obj_visible = []
        obj_hidden =[]
        obj_dict = {}

        types_tool = getToolByName(self, 'portal_types')
        types=types_tool.listContentTypes(by_metatype=1)

        for obj in self._objects:
            # sort out in portal visible and invisible objects in 2 lists
            try:
                types.index(obj['meta_type'])
            except ValueError:
                obj_hidden.append(obj)
            else:
                obj_dict[ obj['id'] ] = obj
                obj_visible.append(obj)


        # unify moving direction
        if delta > 0:
            ids = list(ids)
            ids.reverse()
            obj_visible.reverse()
        counter = 0

        for id in ids:
            try:
                object = obj_dict[id]
            except KeyError:
                raise ValueError('The object with the id "%s" does not exist.'
                                 % id)
            old_position = obj_visible.index(object)
            new_position = max( old_position - abs(delta), min_position )
            if new_position == min_position:
                min_position += 1
            if not old_position == new_position:
                obj_visible.remove(object)
                obj_visible.insert(new_position, object)
                counter += 1

        if counter > 0:
            if delta > 0:
                obj_visible.reverse()
            self._objects = tuple(obj_hidden + obj_visible)

        return counter


    security.declareProtected(ModifyPortalContent, 'getObjectPosition')
    def getObjectPosition(self, id):

        objs = list(self._objects)
        om = [objs.index(om) for om in objs if om['id']==id ]

        if om: # only 1 in list if any
            return om[0]

        raise NotFound('Object %s was not found'%str(id))

    security.declareProtected(ModifyPortalContent, 'moveObjectsUp')
    def moveObjectsUp(self, ids, delta=1, RESPONSE=None):
        """ Move an object up """
        self.moveObjectsByDelta(ids, -delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(ModifyPortalContent, 'moveObjectsDown')
    def moveObjectsDown(self, ids, delta=1, RESPONSE=None):
        """ move an object down """
        self.moveObjectsByDelta(ids, delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(ModifyPortalContent, 'moveObjectsToTop')
    def moveObjectsToTop(self, ids, RESPONSE=None):
        """ move an object to the top """
        self.moveObjectsByDelta( ids, -len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(ModifyPortalContent, 'moveObjectsToBottom')
    def moveObjectsToBottom(self, ids, RESPONSE=None):
        """ move an object to the bottom """
        self.moveObjectsByDelta( ids, len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(ModifyPortalContent, 'moveObjectToPosition')
    def moveObjectToPosition(self, id, position):
        """ Move specified object to absolute position.
        """
        delta = position - self.getObjectPosition(id)
        return self.moveObjectsByDelta(id, delta)

    security.declareProtected(ModifyPortalContent, 'orderObjects')
    def orderObjects(self, key, reverse=None):
        """ Order sub-objects by key and direction.
        """
        ids = [ id for id, obj in sort( self.objectItems(),
                                        ( (key, 'cmp', 'asc'), ) ) ]
        if reverse:
            ids.reverse()
        return self.moveObjectsByDelta( ids, -len(self._objects) )

    # here the implementing of IOrderedContainer ends


    def manage_renameObject(self, id, new_id, REQUEST=None):
        " "
        objidx = self.getObjectPosition(id)
        method = OrderedContainer.inheritedAttribute('manage_renameObject')
        result = method(self, id, new_id, REQUEST)
        self.moveObject(new_id, objidx)

        return result

InitializeClass(OrderedContainer)

class new_OrderedBaseFolder(BaseFolder, OrderedContainer):
    """ An ordered base folder implementation """
    
    __implements__ = (OrderedContainer.__implements__, BaseFolder.__implements__,)

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        OrderedFolder.__init__(self, oid, self.Title())
        BaseFolder.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declarePrivate('manage_renameObject')
    def manage_renameObject(self, item, container):
        BaseFolder.manage_renameObject(self, item, container)
        OrderedContainer.manage_renameObject(self, item, container)


class old_OrderedBaseFolder(BaseObject, Referenceable, OrderedFolder, ExtensibleMetadata):
    """ An ordered base Folder implementation 
        DEPRECATED, may be removed in next releaeses """

    __implements__ = (IBaseFolder, IReferenceable, IExtensibleMetadata,
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

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        Referenceable.manage_afterClone(self, item)
        BaseObject.manage_afterClone(self, item)
        OrderedFolder.manage_afterClone(self, item)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        BaseObject.manage_beforeDelete(self, item, container)
        OrderedFolder.manage_beforeDelete(self, item, container)


if USE_OLD_ORDEREDFOLDER_IMPLEMENTATION:
    OrderedBaseFolder = old_OrderedBaseFolder
else:
    OrderedBaseFolder = new_OrderedBaseFolder
    
InitializeClass(OrderedBaseFolder)
