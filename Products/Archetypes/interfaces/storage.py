from interface import Interface

class IStorage(Interface):
    """Abstraction around the storage of field level data"""

    def getName():
        """return the storage name"""

    def get(name, instance, **kwargs):
        """lookup a value for a given instance stored under 'name'"""

    def set(name, instance, value, **kwargs):
        """set a value under the key 'name' for retrevial by/for
        instance"""

    def unset(name, instance, value, **kwargs):
        """unset a value under the key 'name'.
        used when changing storage for a field."""

class ISQLStorage(IStorage):
    """ Marker interface for distinguishing ISQLStorages """
    pass
    
