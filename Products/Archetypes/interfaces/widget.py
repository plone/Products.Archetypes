from Interface import Interface, Attribute

class IWidget:
    def __call__(instance, context=None):
        """return a rendered fragment that can be included in a larger
        context when called by a renderer.

        instance - the instance this widget is called for
        context  - should implement dict behavior
        """

    def getContext(self, mode, instance):
        """returns any prepaired context or and empty {}
        """

    def Label(self, instance):
        """Returns the label, possibly translated
        """

    def Description(self, instance):
        """Returns the description, possibly translated
        """
