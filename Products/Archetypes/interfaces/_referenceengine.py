from zope.interface import Interface

class IReference(Interface):
    """ Reference """

    def UID():
        """the uid method for compat"""

    # Convenience methods
    def getSourceObject():
        """ returns the source end as object """

    def getTargetObject():
        """ returns the source end as object """

    # Catalog support
    def targetId():
        """ gives the id of the target object """

    def targetTitle():
        """ gives the title of the target object """


    # Policy hooks, subclass away
    def addHook(tool, sourceObject=None, targetObject=None):
        """gets called after reference object has been annotated to the object
        to reject the reference being added raise a ReferenceException """

    def delHook(tool, sourceObject=None, targetObject=None):
        """gets called before reference object gets deleted
        to reject the delete raise a ReferenceException """

    ###
    # OFS Operations Policy Hooks
    # These Hooks are experimental and subject to change
    def beforeTargetDeleteInformSource():
        """called before target object is deleted so
        the source can have a say"""

    def beforeSourceDeleteInformTarget():
        """called when the refering source Object is
        about to be deleted"""

    def _getURL():
        """the url used as the relative path based uid in the catalogs"""


class IContentReference(IReference):
    '''Subclass of Reference to support contentish objects inside references '''

    def getContentObject():
        """ gives the contentish object attached to the reference"""

class IReferenceCatalog(Interface):
    """Marker interface for reference catalog
    """

class IUIDCatalog(Interface):
    """Marker interface for uid catalog
    """
