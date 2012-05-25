from zope.interface import Attribute, Interface


class IArchetypeTool(Interface):
    """This tool manages various kinds of behaviour for Archetype based
    content types. """

    id = Attribute('id', 'Must be set to "archetype_tool"')

    def listRegisteredTypes(inProject=False):
        """Return the list of sorted types.
        """

    def setCatalogsByType(meta_type, catalogList):
        """ associate catalogList with meta_type. (unfortunally not portal_type).

            catalogList is a list of strings with the ids of the catalogs.
            Each catalog is has to be a tool, means unique in site root.
        """

    def getCatalogsByType(meta_type):
        """Return the catalog objects assoicated with a given type.
        """

    def getCatalogsInSite(self):
        """Return a list of ids for objects implementing ZCatalog.
        """
