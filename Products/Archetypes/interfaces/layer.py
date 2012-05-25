from zope.interface import Interface


class ILayer(Interface):
    """Layering support
    """

    def initializeInstance(instance, item=None, container=None):
        """Optionally called to initialize a layer for an entire
        instance
        """

    def initializeField(instance, field):
        """Optionally called to initialize a layer for a given field
        """

    def cleanupField(instance, field):
        """Optionally called to cleanup a layer for a given field
        """

    def cleanupInstance(instance, item=None, container=None):
        """Optionally called to cleanup a layer for an entire
        instance
        """


class ILayerContainer(Interface):
    """An object that contains layers and can use/manipulate them"""

    def registerLayer(name, object):
        """Register an object as providing a new layer under a given
        name
        """

    def registeredLayers():
        """Provides a list of (name, object) layer pairs
        """

    def hasLayer(name):
        """Boolean indicating if the layer is implemented on the
        object
        """

    def getLayerImpl(name):
        """Return an object implementing this layer
        """


class ILayerRuntime(Interface):
    """ Layer Runtime """

    def initializeLayers(instance, item=None, container=None):
        """Optionally process all layers attempting their
        initializeInstance and initializeField methods if they exist
        """

    def cleanupLayers(instance, item=None, container=None):
        """Optionally process all layers attempting their
        cleanupInstance and cleanupField methods if they exist.
        """
