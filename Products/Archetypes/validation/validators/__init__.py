from Products.Archetypes.validation.validators.RegexValidator import RegexValidator
from Products.Archetypes.validation.validators.RangeValidator import RangeValidator

validators = []

from Products.Archetypes.validation.validators.BaseValidators import baseValidators
validators.extend(baseValidators)

from Products.Archetypes.validation.validators.EmptyValidator import validatorList
validators.extend(validatorList)

from Products.Archetypes.validation.validators.SupplValidators import validatorList
validators.extend(validatorList)

def initialize(service):
    for validator in validators:
        service.register(validator)
