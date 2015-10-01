from zope.interface import Interface


class IUtils(Interface):
    """Archetypes utils view
    """

    def translate(value):
        """Use zope.i18n to trnslate values
        Wrapper to be used in pythonscripts
        """
