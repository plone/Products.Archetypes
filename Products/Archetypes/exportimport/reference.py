from zope.component import adapts

from Products.GenericSetup.interfaces import ISetupEnviron

from Products.Archetypes.exportimport import catalog
from Products.Archetypes.interfaces import IReferenceCatalog

NAME = 'reference_catalog'


def importCatalogTool(context):
    """Import catalog.
    """
    catalog.importCatalogTool(context, name=NAME)


def exportCatalogTool(context):
    """Export catalog.
    """
    catalog.exportCatalogTool(context, name=NAME)


class ReferenceCatalogXMLAdapter(catalog.CatalogXMLAdapter):
    """XML im- and exporter for the reference catalog.
    """

    adapts(IReferenceCatalog, ISetupEnviron)

    _LOGGER_ID = NAME
    name = NAME
