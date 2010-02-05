from zope.component import adapts

from Products.GenericSetup.interfaces import ISetupEnviron

from Products.Archetypes.exportimport import catalog
from Products.Archetypes.interfaces import IUIDCatalog

NAME = 'uid_catalog'


def importCatalogTool(context):
    """Import catalog.
    """
    catalog.importCatalogTool(context, name=NAME)


def exportCatalogTool(context):
    """Export catalog.
    """
    catalog.exportCatalogTool(context, name=NAME)


class UIDCatalogXMLAdapter(catalog.CatalogXMLAdapter):
    """XML im- and exporter for the UID catalog.
    """

    adapts(IUIDCatalog, ISetupEnviron)

    _LOGGER_ID = NAME
    name = NAME
