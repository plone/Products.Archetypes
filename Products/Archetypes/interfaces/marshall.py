from Products.Archetypes.interfaces.layer import ILayer

class IMarshall(ILayer):
    """De/Marshall data.
    demarshall returns a dict to the calling method so that it can
    place the values into the object as needed

    Marshall knows about the schema on instance and can directly pull
    the value and return a data object.
    """

    def demarshall(instance, data, **kwargs):
        """given the blob 'data' demarshall it into a dict of k/v
        pairs"""


    def marshall(instance, **kwargs):
        """returns a tuple of content-type, length, and data"""
