from plone.uuid.interfaces import IUUIDAware

class IReferenceable(IUUIDAware):
    """ Referenceable """

    def getRefs(relationship=None):
        """get all the referenced objects for this object"""

    def getBRefs(relationship=None):
        """get all the back referenced objects for this object"""

    def getReferences(relationship=None):
        """ alias for getRefs """

    def getBackReferences(relationship=None):
        """ alias for getBRefs """

    def getReferenceImpl(relationship=None):
        """ returns the references as objects for this object """

    def getBackReferenceImpl(relationship=None):
        """ returns the back references as objects for this object """

    def UID():
        """ Unique ID """

    def reference_url():
        """like absoluteURL, but return a link to the object with this UID"""

    def hasRelationshipTo(target, relationship=None):
        """test is a relationship exists between objects"""

    def addReference(target, relationship=None, **kwargs):
        """add a reference to target. kwargs are metadata"""

    def deleteReference(target, relationship=None):
        """delete a ref to target"""

    def deleteReferences(relationship=None):
        """delete all references from this object"""

    def getRelationships():
        """list all the relationship types this object has refs for"""
