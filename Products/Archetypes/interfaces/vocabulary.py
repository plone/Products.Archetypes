from interface import Interface, Attribute

class IVocabulary(Interface):
    """ interface for vocabularies used in fields """
    
    def getDisplayList(self, instance):
        """ returns a object of class DisplayList as defined in 
            Products.Archetypes.utils. 
            
            The instance of the content class is given as parameter.
        """
    
