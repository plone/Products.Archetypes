class ValidatorError(Exception): pass
class UnknowValidatorError(ValidatorError): pass
class FalseValidatorError(ValidatorError): pass
class AlreadyRegisteredValidatorError(ValidatorError): pass