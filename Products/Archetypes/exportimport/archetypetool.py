from sets import Set
from zope.component import getUtility
from zope.component import queryUtility

from Products.Archetypes.interfaces import IArchetypeTool
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects


class ArchetypeToolXMLAdapter(XMLAdapterBase):
    """Mode in- and exporter for ArchetypesTool.
    """

    __used_for__ = IArchetypeTool

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node=self._doc.createElement('archetypetool')
        node.appendChild(self._extractCatalogSettings())

        self._logger.info('ArchetypeTool settings exported.')
        return node


    def _importNode(self, node):
        if self.environ.shouldPurge():
            self._purgeCatalogSettings()

        self._initCatalogSettings(node)
        self._logger.info('ArchetypeTool settings imported.')
    


    def _purgeCatalogSettings(self):
        self.context.catalog_map.clear()


    def _initCatalogSettings(self, node):
        for child in node.childNodes:
            if child.nodeName=='catalogmap':
                for type in child.getElementsByTagName('type'):
                    portaltype=type.getAttribute('portal_type')
                    catalogs=[e.getAttribute('value') \
                              for e in type.getElementsByTagName('catalog')]
                    already = [cat.getId() for cat in
                               self.context.getCatalogsByType(portaltype)]
                    catalogs=Set(catalogs + already)
                    self.context.setCatalogsByType(portaltype, list(catalogs))


    def _extractCatalogSettings(self):
        node=self._doc.createElement('catalogmap')
        for type in self.context.listRegisteredTypes(True):
            child=self._doc.createElement('type')
            child.setAttribute('portal_type', type['name'])
            for cat in self.context.getCatalogsByType(type['name']):
                sub=self._doc.createElement('catalog')
                sub.setAttribute('value', cat.id)
                child.appendChild(sub)
            node.appendChild(child)

        return node


def importArchetypeTool(context):
    """Import Archetype Tool configuration.
    """
    site = context.getSite()
    tool = getUtility(IArchetypeTool)

    importObjects(tool, '', context)


def exportArchetypeTool(context):
    """Export Archetype Tool configuration.
    """
    site = context.getSite()
    tool = queryUtility(IArchetypeTool)
    if tool is None:
        logger = context.getLogger("archetypestool")
        logger.info("Nothing to export.")
        return

    exportObjects(tool, '', context)
