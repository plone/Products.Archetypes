from Products.Archetypes.interfaces.layer import ILayer

class IMarshall(ILayer):
    """De/Marshall data.
    """

    def demarshall(instance, data, **kwargs):
        """Given the blob 'data' demarshall it and modify 'instance'
        accordingly if possible
        """

    def marshall(instance, **kwargs):
        """Returns a tuple of content-type, length, and data
        """
