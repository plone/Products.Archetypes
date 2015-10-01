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
