from Products.CMFCore.exportimport.typeinfo import TypeInformationXMLAdapter \
     as TypeInfoXMLAdapterBase
from Products.CMFCore.utils import getToolByName

class TypeInformationXMLAdapter(TypeInfoXMLAdapterBase):
    """
    XML im- and exporter for TypeInformation, adds support for
    CatalogMultiplex.
    """
    def _exportNode(self):
        """
        Export the object as a DOM node.
        """
        node = TypeInfoXMLAdapterBase._exportNode(self)
        node.appendChild(self._extractCatalogs())
        return node

    def _importNode(self, node):
        """
        Import the object from the DOM node.
        """
        TypeInfoXMLAdapterBase._importNode(self, node)
        self._initCatalogs(node)

    def _extractCatalogs(self):
        """
        Figure out which catalogs the type is registered with.
        """
        fragment = self._doc.createDocumentFragment()
        attool = getToolByName(self.context, 'archetype_tool', None)
        if attool is None:
            return fragment
        catalogs = attool.getCatalogsByType(self.context.getId())
        for catalog in catalogs:
            child = self._doc.createElement('catalog')
            child.setAttribute('id', catalog.getId())
            fragment.appendChild(child)
        return fragment

    def _initCatalogs(self, node):
        """
        Register the type w/ the appropriate catalogs in the
        archetype_tool.
        """
        attool = getToolByName(self.context, 'archetype_tool', None)
        if attool is None:
            return
        catalog_ids = []
        for child in node.childNodes:
            if child.nodeName != 'catalog':
                continue
            catalog_ids.append(child.getAttribute('id'))
        attool.setCatalogsByType(self.context.getId(), catalog_ids)
        
