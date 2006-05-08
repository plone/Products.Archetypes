from Products.Archetypes.interfaces import IArchetypeTool
from Products.GenericSetup.utils import XMLAdapterBase


class ArchetypeToolXMLAdapater(XMLAdapterBase):
    """Mode in- and exporter for ArchetypesTool.
    """

    __used_for__ = IArchetypeTool

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node=self._getObjectNode('object')
        node.appendChild(self._extractCatalogSettings())
        self._logger.info('ArchetypeTool settings exported.')
        return node


    def _importNode(self, node):
        self._initCatalogSettings(node)
        self._logger.info('ArchetypeTool settings imported.')
    

    def _initCatalogSettings(self, node):
        import pdb
        pdb.set_trace()


    def _extractCatalogSettings(self):
        fragment = self._doc.createDocumentFragment()
        for type in self.context.listRegisteredTypes(True):
            child=self._doc.createElement('type')
            child.setAttribute('meta_type', type['name'])
            for cat in self.context.getCatalogsByType(type['name']):
                sub=self._doc.createElement('catalog')
                sub.setAttribute('value', cat.id)
                child.appendChild(sub)
            fragment.appendChild(child)

        return fragment



