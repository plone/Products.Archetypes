from interface import Interface, Attribute

class IValidationService(Interface):

    def validate(name_or_validator, value, *args, **kwargs):
        """call the validator of a given name"""

    def validatorFor(name_or_validator):
        """return the validator for a given name"""

    def register(validator):
        """load a validator for access by name"""

    def unregister(name_or_validator):
        """unregisters a validator by name"""