from types import StringType

from Products.Archetypes.bases.basefolder import BaseFolder
from Products.Archetypes.bases.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.interfaces.orderedfolder import IOrderedFolder
from DocumentTemplate import sequence

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces.Dynamic import DynamicType
from Products.CMFDefault.SkinnedFolder import SkinnedFolder
from Products.CMFCore import CMFCorePermissions

# this import can change with Zope 2.7 to
try:
    from OFS.IOrderSupport import IOrderedContainer as IZopeOrderedContainer
    hasZopeOrderedSupport=1
except ImportError:
    hasZopeOrderedSupport=0
    
try:
    from zExceptions import NotFound
except ImportError:
    class NotFound(Exception): pass

# atm its safer defining an own so we need an ugly hack to make Archetypes
# OrderedBaseFolder work without Plone 2.0
try:
    from Products.CMFPlone.interfaces.OrderedContainer import IOrderedContainer
except:
    from Products.Archetypes.interfaces.orderedfolder import IOrderedContainer

class OrderedContainer:

    if hasZopeOrderedSupport:
        # got the IOrderedContainer interface from zope 2.7, too
        # make shure this implementation fullfilles both interfaces
        __implements__  = IOrderedContainer, IZopeOrderedContainer
    else:
        __implements__  = IOrderedContainer

    security = ClassSecurityInfo()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObject')
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

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectsByDelta')
    def moveObjectsByDelta(self, ids, delta, subset_ids=None):
        """ Move specified sub-objects by delta.

        XXX zope 2.7 has a new argument subset_ids which isn't handled by this
        implementation
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


    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'getObjectPosition')
    def getObjectPosition(self, id):

        objs = list(self._objects)
        om = [objs.index(om) for om in objs if om['id']==id ]

        if om: # only 1 in list if any
            return om[0]

        raise NotFound(str(id))

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectsUp')
    def moveObjectsUp(self, ids, delta=1, RESPONSE=None):
        """ Move an object up """
        self.moveObjectsByDelta(ids, -delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectsDown')
    def moveObjectsDown(self, ids, delta=1, RESPONSE=None):
        """ move an object down """
        self.moveObjectsByDelta(ids, delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectsToTop')
    def moveObjectsToTop(self, ids, RESPONSE=None):
        """ move an object to the top """
        self.moveObjectsByDelta( ids, -len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectsToBottom')
    def moveObjectsToBottom(self, ids, RESPONSE=None):
        """ move an object to the bottom """
        self.moveObjectsByDelta( ids, len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'moveObjectToPosition')
    def moveObjectToPosition(self, id, position):
        """ Move specified object to absolute position.
        """
        delta = position - self.getObjectPosition(id)
        return self.moveObjectsByDelta(id, delta)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'orderObjects')
    def orderObjects(self, key, reverse=None):
        """ Order sub-objects by key and direction.

        Key can be an attribute or a method
        """
        ids = [ id for id, obj in sequence.sort( self.objectItems(),
                                        ( (key, 'cmp', 'asc'), ) ) ]
        if reverse:
            ids.reverse()
        return self.moveObjectsByDelta( ids, -len(self._objects) )

    # here the implementing of IOrderedContainer ends


InitializeClass(OrderedContainer)

class OrderedBaseFolder(BaseFolder, OrderedContainer):
    """ An ordered base folder implementation """

    __implements__ = OrderedContainer.__implements__,\
                     BaseFolder.__implements__, DynamicType

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        BaseFolder.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename the object
        """
        objidx = self.getObjectPosition(id)
        result = BaseFolder.manage_renameObject(self, id, new_id, REQUEST)
        self.moveObject(new_id, objidx)

        return result


InitializeClass(OrderedBaseFolder)

OrderedBaseFolderSchema = OrderedBaseFolder.schema

__all__ = ('OrderedBaseFolder', 'OrderedContainer', 'OrderedBaseFolderSchema',)
