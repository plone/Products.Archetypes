from interface import Interface, Attribute

class IValidator(Interface):

    name = Attribute("name of the validator")
    title = Attribute("title or name of the validator")
    description = Attribute("description of the validator")

    def __call__(value, *args, **kwargs):
        """return True if valid, error string if not"""


class IValidationChain(IValidator):
    """Marker interface for a chain
    """
