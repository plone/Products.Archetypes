from interface import Interface, Attribute

class ITemplateMixin(Interface):
    """Marker interface for TemplateMixin
    """
    
    default_view = Attribute('')
    suppl_views = Attribute('')

    def getLayout():
        """
        """

    def getDefaultLayout():
        """
        """
        
    def getTemplateFor(pt, default='base_view'):
        """
        """
