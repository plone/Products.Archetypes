class ObjectFieldException(Exception):
    pass

class TextFieldException(ObjectFieldException):
    pass

class FileFieldException(ObjectFieldException):
    pass

class ReferenceException(Exception):
    pass

class SchemaException(Exception):
    pass


# validator
class ValidatorError(Exception):
    pass

class UnknowValidatorError(ValidatorError):
    pass

class FalseValidatorError(ValidatorError):
    pass

class AlreadyRegisteredValidatorError(ValidatorError):
    pass
