try:
    from Products.Archetypes.validation.interfaces.IValidationService import IValidationService
    from Products.Archetypes.validation.interfaces.IValidator import IValidator
except ImportError:
    from validation.interfaces.IValidationService import IValidationService
    from validation.interfaces.IValidator import IValidator

from exceptions import UnknowValidatorError, FalseValidatorError, AlreadyRegisteredValidatorError
from types import StringType

class Service:
    __implements__ = IValidationService

    def __init__(self):
        self._validator = {}

    def validate(self, name_or_validator, value, *args, **kwargs):
        v = self.validatorFor(name_or_validator)
        return v(value, *args, **kwargs)

    __call__ = validate

    def validatorFor(self, name_or_validator):
        if type(name_or_validator) is StringType:
            try:
                return self._validator[name_or_validator]
            except KeyError:
                raise UnknowValidatorError, name_or_validator
        elif IValidator.isImplementedBy(name_or_validator):
            return name_or_validator
        else:
            raise FalseValidatorError, name_or_validator

    def register(self, validator):
        if not IValidator.isImplementedBy(validator):
            raise FalseValidatorError, validator
        name = validator.name
        # The following code prevents refreshing
        ##if self._validator.has_key(name):
        ##    raise AlreadyRegisteredValidatorError, name
        self._validator[name] = validator

    def items(self):
        return self._validator.items()

    def keys(self):
        return [k for k, v in self.items()]

    def values(self):
        return [v for k, v in self.items()]

    def unregister(self, name_or_validator):
        if type(name_or_validator) is StringType:
            name = name_or_validator
        elif IValidator.isImplementedBy(name_or_validator):
            name = name_or_validator.name
        if self._validator.has_key(name):
            del self._validator[name]
