"""
OrderedBaseFolder derived from OrderedFolder by Stephan Richter, iuveno AG.
OrderedFolder adapted to Zope 2.7 style interface by Jens.KLEIN@jensquadrat.de
"""
from types import StringType

from Products.Archetypes.BaseFolder import BaseFolder
from Products.Archetypes.Referenceable import Referenceable
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.BaseObject import BaseObject
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from Products.Archetypes.interfaces.base import IBaseFolder
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
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
    from interfaces.orderedfolder import IOrderedContainer

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
            old_position = subset_ids.index(id)
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
        cmf_meta_types = ttool.listContentTypes(by_metatype=1)
        return [obj['id'] for obj in objs if obj['meta_type'] in cmf_meta_types ]

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'getObjectPosition')
    def getObjectPosition(self, id):

        objs = list(self._objects)
        om = [objs.index(om) for om in objs if om['id']==id ]

        if om: # only 1 in list if any
            return om[0]

        raise NotFound, 'Object %s was not found' % str(id)

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
        """ rename the object """
        objidx = self.getObjectPosition(id)
        result = BaseFolder.manage_renameObject(self, id, new_id, REQUEST)
        self.moveObject(new_id, objidx)

        return result

InitializeClass(OrderedBaseFolder)

OrderedBaseFolderSchema = OrderedBaseFolder.schema

__all__ = ('OrderedBaseFolder', 'OrderedContainer', 'OrderedBaseFolderSchema',)
