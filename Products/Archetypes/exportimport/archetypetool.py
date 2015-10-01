from zope.component import adapts

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase


from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.interfaces import IArchetypeTool


class ArchetypeToolXMLAdapter(XMLAdapterBase):
    """Mode in- and exporter for ArchetypesTool.
    """

    adapts(IArchetypeTool, ISetupEnviron)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._doc.createElement('archetypetool')
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
            if child.nodeName == 'catalogmap':
                for type in child.getElementsByTagName('type'):
                    portaltype = type.getAttribute('portal_type')
                    catalogs = [e.getAttribute('value')
                                for e in type.getElementsByTagName('catalog')]
                    already = [cat.getId() for cat in
                               self.context.getCatalogsByType(portaltype)]
                    catalogs = set(catalogs + already)
                    self.context.setCatalogsByType(portaltype, list(catalogs))

    def _extractCatalogSettings(self):
        node = self._doc.createElement('catalogmap')
        for type in self.context.listRegisteredTypes(True):
            child = self._doc.createElement('type')
            child.setAttribute('portal_type', type['name'])
            for cat in self.context.getCatalogsByType(type['name']):
                sub = self._doc.createElement('catalog')
                sub.setAttribute('value', cat.id)
                child.appendChild(sub)
            node.appendChild(child)

        return node


def importArchetypeTool(context):
    """Import Archetype Tool configuration.
    """
    site = context.getSite()
    logger = context.getLogger("archetypetool")
    tool = getToolByName(site, TOOL_NAME, None)
    if tool is None:
        return

    importObjects(tool, '', context)
    logger.info("Archetype tool imported.")


def exportArchetypeTool(context):
    """Export Archetype Tool configuration.
    """
    site = context.getSite()
    logger = context.getLogger("archetypetool")
    tool = getToolByName(site, TOOL_NAME, None)
    if tool is None:
        return

    exportObjects(tool, '', context)
    logger.info("Archetype tool exported.")
