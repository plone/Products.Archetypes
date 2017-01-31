"""
Archetypes setup handlers.
"""
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import UID_CATALOG
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Prevents uninstall profile from showing up in the profile list
        when creating a Plone site.

        """
        return [
            u'Products.Archetypes:uninstall',
        ]


def install_uidcatalog(out, site, rebuild=False):
    catalog = getToolByName(site, UID_CATALOG)

    index_defs = (('UID', 'FieldIndex'),
                  ('Type', 'FieldIndex'),
                  ('id', 'FieldIndex'),
                  ('Title', 'FieldIndex'),  # used for sorting
                  ('portal_type', 'FieldIndex'),)
    metadata_defs = ('UID', 'Type', 'id', 'Title', 'portal_type', 'meta_type')
    reindex = False

    for indexName, indexType in index_defs:
        if indexName not in catalog.indexes():
            catalog.addIndex(indexName, indexType, extra=None)
            reindex = True

    for metadata in metadata_defs:
        if indexName not in catalog.schema():
            catalog.addColumn(metadata)
            reindex = True
    if reindex:
        catalog.manage_reindexIndex(index_defs)


def install_referenceCatalog(out, site, rebuild=False):
    catalog = getToolByName(site, REFERENCE_CATALOG)
    reindex = False

    index_names = ('UID', 'sourceUID', 'targetUID', 'relationship', 'targetId')
    for indexName, indexType in zip(index_names, ('FieldIndex',) * 5):
        if indexName not in catalog.indexes():
            catalog.addIndex(indexName, indexType, extra=None)
            reindex = True
        if indexName not in catalog.schema():
            catalog.addColumn(indexName)
            reindex = True
    if reindex:
        catalog.manage_reindexIndex(index_names)


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
