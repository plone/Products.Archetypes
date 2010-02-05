from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.ZCatalog.exportimport import ZCatalogXMLAdapter


def importCatalogTool(context, name='portal_catalog'):
    """Import catalog.
    """
    site = context.getSite()
    tool = getToolByName(site, name, None)
    if tool is not None:
        importObjects(tool, '', context)


def exportCatalogTool(context, name='portal_catalog'):
    """Export catalog.
    """
    site = context.getSite()
    tool = getToolByName(site, name, None)
    if tool is None:
        logger = context.getLogger('catalog')
        logger.info('Nothing to export.')
        return

    exportObjects(tool, '', context)


class CatalogXMLAdapter(ZCatalogXMLAdapter):
    """XML im- and exporter for a catalog.
    """

    def _initIndexes(self, node):
        added = []
        zcatalog = self.context

        for child in node.childNodes:
            if child.nodeName != 'index':
                continue
            if child.hasAttribute('deprecated'):
                continue

            idx_id = str(child.getAttribute('name'))

            if idx_id not in zcatalog.indexes():
                added.append(idx_id)

        ZCatalogXMLAdapter._initIndexes(self, node)

        if len(added) > 0:
            zcatalog.reindexIndex(tuple(added), None)

    def _initColumns(self, node):
        for child in node.childNodes:
            if child.nodeName != 'column':
                continue
            col = str(child.getAttribute('value'))
            if child.hasAttribute('remove'):
                # Remove the column if it is there
                if col in self.context.schema()[:]:
                    self.context.delColumn(col)
                continue
            if col not in self.context.schema()[:]:
                self.context.addColumn(col)
                # If we added a new column we need to update the
                # metadata even if this will take a while
                self.context.refreshCatalog()
