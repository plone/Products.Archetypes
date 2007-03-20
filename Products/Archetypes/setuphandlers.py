"""
Archetypes setup handlers.
"""

from zope.component import getUtility
from zope.component import queryUtility

from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IReferenceCatalog
from Products.Archetypes.interfaces import IUIDCatalog


def install_uidcatalog(out, rebuild=False):
    catalog = queryUtility(IUIDCatalog)

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


def install_referenceCatalog(out, rebuild=False):
    catalog = queryUtility(IReferenceCatalog)
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


def install_templates(out):
    at = getUtility(IArchetypeTool)
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
    install_uidcatalog(out)
    install_referenceCatalog(out)
    install_templates(out)
