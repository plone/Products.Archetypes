from zope.interface import Interface


class IEditForm(Interface):
    """Archetypes edit form view
    """

    def isTemporaryObject():
        """"""

    def isMultiPageSchema():
        """ Returns true if the schema for the current object should be
        rendered on multiple pages.
        """

    def fieldsets():
        """"""

    def fields(fieldsets):
        """"""

    def getTranslatedSchemaLabel(schema):
        """ Returns the translated title for the given schema. """

    def normalizeString(text):
        """"""
