from Products.Archetypes.interfaces.layer import ILayerContainer
from ExtensionClass import Base
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from zope.interface import implementer


@implementer(ILayerContainer)
class DefaultLayerContainer(Base):

    security = ClassSecurityInfo()

    def __init__(self):
        self._layers = {}

    security.declarePrivate('registerLayer')

    def registerLayer(self, name, object):
        self._layers[name] = object

    security.declarePrivate('registeredLayers')

    def registeredLayers(self):
        return self._layers.items()

    security.declarePrivate('hasLayer')

    def hasLayer(self, name):
        return name in self._layers.keys()

    security.declarePrivate('getLayerImpl')

    def getLayerImpl(self, name):
        return self._layers[name]

InitializeClass(DefaultLayerContainer)
