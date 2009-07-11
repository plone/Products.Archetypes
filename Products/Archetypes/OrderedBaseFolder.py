"""
OrderedBaseFolder derived from OrderedFolder by Stephan Richter, iuveno AG.
OrderedFolder adapted to Zope 2.7 style interface by Jens.KLEIN@jensquadrat.de
"""
from zope.interface import implements
from types import StringType
from zope.interface import implements

from Products.Archetypes.BaseFolder import BaseFolder
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from DocumentTemplate import sequence

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.interfaces import IOrderedContainer

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFCore import permissions

from zExceptions import NotFound


class OrderedContainer:

    implements(IOrderedContainer)

    security = ClassSecurityInfo()

    security.declareProtected(permissions.ModifyPortalContent, 'moveObject')
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

    # TODO here the implementing of IOrderedContainer starts
    # this should be replaced by mixing in the 2.7 specific class
    # OSF.OrderedContainer.OrderedContainer

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectsByDelta')
    def moveObjectsByDelta(self, ids, delta, subset_ids=None):
        """ Move specified sub-objects by delta.
        """
        if type(ids) is StringType:
            ids = (ids,)
        min_position = 0
        objects = list(self._objects)
        if subset_ids == None:
            # OLD: subset_ids = [ obj['id'] for obj in objects ]
            subset_ids = self.getCMFObjectsSubsetIds(objects)
        else:
            subset_ids = list(subset_ids)
        # unify moving direction
        if delta > 0:
            ids = list(ids)
            ids.reverse()
            subset_ids.reverse()
        counter = 0

        for id in ids:
            try:
                old_position = subset_ids.index(id)
            except ValueError:
                continue
            new_position = max( old_position - abs(delta), min_position )
            if new_position == min_position:
                min_position += 1
            if not old_position == new_position:
                subset_ids.remove(id)
                subset_ids.insert(new_position, id)
                counter += 1

        if counter > 0:
            if delta > 0:
                subset_ids.reverse()
            obj_dict = {}
            for obj in objects:
                obj_dict[ obj['id'] ] = obj
            pos = 0
            for i in range( len(objects) ):
                if objects[i]['id'] in subset_ids:
                    try:
                        objects[i] = obj_dict[ subset_ids[pos] ]
                        pos += 1
                    except KeyError:
                        raise ValueError('The object with the id "%s" does '
                                         'not exist.' % subset_ids[pos])
            self._objects = tuple(objects)

        return counter

    security.declarePrivate('getCMFObjectsSubsetIds')
    def getCMFObjectsSubsetIds(self, objs):
        """Get the ids of only cmf objects (used for moveObjectsByDelta)
        """
        ttool = getToolByName(self, 'portal_types')
        cmf_meta_types = [ti.Metatype() for ti in ttool.listTypeInfo()]
        return [obj['id'] for obj in objs if obj['meta_type'] in cmf_meta_types ]

    security.declareProtected(permissions.ModifyPortalContent, 'getObjectPosition')
    def getObjectPosition(self, id):

        objs = list(self._objects)
        om = [objs.index(om) for om in objs if om['id']==id ]

        if om: # only 1 in list if any
            return om[0]

        raise NotFound, 'Object %s was not found' % str(id)

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectsUp')
    def moveObjectsUp(self, ids, delta=1, RESPONSE=None):
        """ Move an object up """
        self.moveObjectsByDelta(ids, -delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectsDown')
    def moveObjectsDown(self, ids, delta=1, RESPONSE=None):
        """ move an object down """
        self.moveObjectsByDelta(ids, delta)
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectsToTop')
    def moveObjectsToTop(self, ids, RESPONSE=None):
        """ move an object to the top """
        self.moveObjectsByDelta( ids, -len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectsToBottom')
    def moveObjectsToBottom(self, ids, RESPONSE=None):
        """ move an object to the bottom """
        self.moveObjectsByDelta( ids, len(self._objects) )
        if RESPONSE is not None:
            RESPONSE.redirect('manage_workspace')

    security.declareProtected(permissions.ModifyPortalContent, 'moveObjectToPosition')
    def moveObjectToPosition(self, id, position):
        """ Move specified object to absolute position.
        """
        delta = position - self.getObjectPosition(id)
        return self.moveObjectsByDelta(id, delta)

    security.declareProtected(permissions.ModifyPortalContent, 'orderObjects')
    def orderObjects(self, key, reverse=None):
        """ Order sub-objects by key and direction.
        """
        ids = [ id for id, obj in sequence.sort( self.objectItems(),
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


class OrderedBaseFolder(BaseFolder, OrderedContainer):
    """ An ordered base folder implementation """

    implements(IDynamicType)

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        #call skinned first cause baseobject will set new defaults on
        #those attributes anyway
        BaseFolder.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declareProtected(permissions.ModifyPortalContent, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """ rename the object """
        objidx = self.getObjectPosition(id)
        result = BaseFolder.manage_renameObject(self, id, new_id, REQUEST)
        self.moveObject(new_id, objidx)

        return result

InitializeClass(OrderedBaseFolder)

OrderedBaseFolderSchema = OrderedBaseFolder.schema

__all__ = ('OrderedBaseFolder', 'OrderedContainer', 'OrderedBaseFolderSchema',)
