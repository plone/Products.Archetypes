from Products.Archetypes.ReferenceEngine import Reference
from Products.Archetypes.exceptions import ReferenceException

class HoldingReference(Reference):
    def beforeTargetDeleteInformSource(self):
        raise ReferenceException, ("Can't delete target, "
                                   "its held by %s" %
                                   self.getSourceObject().absolute_url())

class CascadeReference(Reference):
    def beforeSourceDeleteInformTarget(self):
        tObj = self.getTargetObject()
        parent = tObj.aq_parent
        parent._delObject(tObj.id)


FOLDERISH_REFERENCE="at_folder_reference"
class FolderishReference(Reference):
    """Used by reference folder under the covers of the folderish API"""

    def __init__(self, id, sid, tid,
                 relationship=FOLDERISH_REFERENCE, **kwargs):
        Reference.__init__(self, id, sid, tid, relationship, **kwargs)

    def beforeSourceDeleteInformTarget(self):
        # The idea is that a reference folder would be
        # incrementing the reference count on its children
        # but not actually, placefully contain the object.
        # if the count is not 1 (meaning the last reference)
        # then we reject the delete
        if len(self.getTargetObject().getBRefs(FOLDERISH_REFERENCE)) != 1:
            raise ReferenceException, ("Can't delete target, "
                                       "its held by %s" %
                                       self.getSourceObject().absolute_url())
