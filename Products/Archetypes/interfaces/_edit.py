from zope.interface import Interface

class IEdit(Interface):
    """ Edit """

    def isMultiPageSchema():
        """ Returns true if the schema for the current object should be
        rendered on multiple pages.
        """

    def getTranslatedSchemaLabel(schema):
        """ Returns the translated title for the given schema. """
