from zope.interface import Interface, Attribute


class ITemplateMixin(Interface):
    """Marker interface for TemplateMixin
    """

    default_view = Attribute('')
    suppl_views = Attribute('')

    def getLayout():
        """
        @return string for current layout
        """

    def getDefaultLayout():
        """
        @return string for default layout
        """

    def getTemplateFor(pt, default='base_view'):
        """
        """
