"""
Archetypes setup handlers.
"""

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import TOOL_NAME, REFERENCE_CATALOG, UID_CATALOG

def install_uidcatalog(out, site, rebuild=False):
    catalog = getToolByName(site, UID_CATALOG)

    index_defs= (('UID', 'FieldIndex'),
                 ('Type', 'FieldIndex'),
                 ('id', 'FieldIndex'),
                 ('Title', 'FieldIndex'), # used for sorting
                 ('portal_type', 'FieldIndex'),)
    metadata_defs = ('UID', 'Type', 'id', 'Title', 'portal_type', 'meta_type')
    reindex = False

    for indexName, indexType in index_defs:
        if indexName not in catalog.indexes():
            catalog.addIndex(indexName, indexType, extra=None)
            reindex = True

    for metadata in metadata_defs:
        if not indexName in catalog.schema():
            catalog.addColumn(metadata)
            reindex = True
    if reindex:
        catalog.manage_reindexIndex()


def install_referenceCatalog(out, site, rebuild=False):
    catalog = getToolByName(site, REFERENCE_CATALOG)
    reindex = False

    for indexName, indexType in (('UID', 'FieldIndex'),
                                 ('sourceUID', 'FieldIndex'),
                                 ('targetUID', 'FieldIndex'),
                                 ('relationship', 'FieldIndex'),
                                 ('targetId', 'FieldIndex'),):
        if not indexName in catalog.indexes():
            catalog.addIndex(indexName, indexType, extra=None)
            reindex = True
        if not indexName in catalog.schema():
            catalog.addColumn(indexName)
            reindex = True
    if reindex:
        catalog.manage_reindexIndex()


def install_templates(out, site):
    at = getToolByName(site, TOOL_NAME)
    at.registerTemplate('base_view', 'Base View')


def setupArchetypes(context):
    """
    Setup Archetypes step.
    """
    # Only run step if a flag file is present (e.g. not an extension profile)
    if context.readDataFile('archetypes-various.txt') is None:
        return
    out = []
    site = context.getSite()
    install_uidcatalog(out, site)
    install_referenceCatalog(out, site)
    install_templates(out, site)
