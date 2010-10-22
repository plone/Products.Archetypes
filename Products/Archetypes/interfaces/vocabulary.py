from zope.interface import Interface, Attribute

class IVocabulary(Interface):
    """ interface for vocabularies used in fields """

    def getDisplayList(self, instance):
        """ returns an object of class DisplayList as defined in
            Products.Archetypes.utils.

            The instance of the content is given as parameter.
        """

    def getVocabularyDict(self, instance):
        """ returns the vocabulary as a dictionary with a string key and a
            string value. If it is not a flat vocabulary, the value is a
            tuple with a string and a sub-dictionary with the same format
            (or None if its a leave).

            Example for a flat vocabulary-dictionary:
            {'key1':'Value 1', 'key2':'Value 2'}

            Example for a hierachical:
            {'key1':('Value 1',{'key1.1':('Value 1.1',None)}), 'key2':('Value 2',None)}

            The instance of the content is given as parameter.
        """

    def isFlat(self):
        """ returns true if the underlying vocabulary is flat, otherwise
            if its hierachical (tree-like) it returns false.
        """

    def showLeafsOnly(self):
        """ returns true for flat vocabularies. In hierachical (tree-like)
            vocabularies it defines if only leafs should be displayed, or
            knots and leafs.
        """
