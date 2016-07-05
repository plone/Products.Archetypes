""" A base/mixin class for Archetype folders with order support

OrderedBaseFolder derived from OrderedFolder by Stephan Richter, iuveno AG.
"""

from zope.interface import implementer

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.OrderSupport import OrderSupport
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFCore import permissions
from zExceptions import NotFound

from Products.Archetypes.BaseFolder import BaseFolder
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata


class OrderedContainer(OrderSupport):
    """ Archetype specific additions and changes to OFS.OrderSupport
    """

    security = ClassSecurityInfo()

    security.declareProtected(permissions.ModifyPortalContent, 'moveObject')

    def moveObject(self, id, position):
        obj_idx = self.getObjectPosition(id)
        if obj_idx == position:
            return None
        elif position < 0:
            position = 0

        metadata = list(self._objects)
        obj_meta = metadata.pop(obj_idx)
        metadata.insert(position, obj_meta)
        self._objects = tuple(metadata)

    security.declarePrivate('getCMFObjectsSubsetIds')

    def getIdsSubset(self, objs):
        # Get the ids of only cmf objects (used for moveObjectsByDelta).
        ttool = getToolByName(self, 'portal_types')
        cmf_meta_types = [ti.Metatype() for ti in ttool.listTypeInfo()]
        return [obj['id'] for obj in objs
                if obj['meta_type'] in cmf_meta_types]

    # BBB
    getCMFObjectsSubsetIds = getIdsSubset

    security.declareProtected(
        permissions.ModifyPortalContent, 'getObjectPosition')

    def getObjectPosition(self, id):
        try:
            pos = OrderSupport.getObjectPosition(self, id)
        except ValueError:
            raise NotFound, 'Object %s was not found' % str(id)
        return pos

InitializeClass(OrderedContainer)


@implementer(IDynamicType)
class OrderedBaseFolder(BaseFolder, OrderedContainer):
    """ An ordered base folder implementation """

    security = ClassSecurityInfo()

    def __init__(self, oid, **kwargs):
        # call skinned first cause baseobject will set new defaults on
        # those attributes anyway
        BaseFolder.__init__(self, oid, **kwargs)
        ExtensibleMetadata.__init__(self)

    security.declareProtected(
        permissions.ModifyPortalContent, 'manage_renameObject')

    def manage_renameObject(self, id, new_id, REQUEST=None):
        """ rename the object """
        objidx = self.getObjectPosition(id)
        result = BaseFolder.manage_renameObject(self, id, new_id, REQUEST)
        self.moveObject(new_id, objidx)

        return result

InitializeClass(OrderedBaseFolder)

OrderedBaseFolderSchema = OrderedBaseFolder.schema

__all__ = ('OrderedBaseFolder', 'OrderedContainer', 'OrderedBaseFolderSchema',)
