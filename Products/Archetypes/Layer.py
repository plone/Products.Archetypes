from Products.Archetypes.interfaces.layer import ILayerContainer

class DefaultLayerContainer:
    __implements__ = ILayerContainer

    def __init__(self):
        self._layers = {}

        #ILayerContainer
    def registerLayer(self, name, object):
        self._layers[name] = object

    def registeredLayers(self):
        return self._layers.items()

    def hasLayer(self, name):
        return name in self._layers.keys()

    def getLayerImpl(self, name):
        return self._layers[name]
