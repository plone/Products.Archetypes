try:
    from validation.interfaces import ivalidator
    from validation import validation
except ImportError:
    from Products.validation.interfaces import ivalidator
    from Products.validation import validation
from DateTime import DateTime

class DateValidator:
    __implements__ = (ivalidator,)

    def __init__(self, name):
        self.name = name

    def __call__(self, value, *args, **kwargs):
        if not value:
            return """Validation Failed(%s): value is empty or not informed (%s).""" % (self.name,
                                                                                        repr(value))
        if not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                return """Validation Failed(%s): could not convert %s to a date.""" %(self.name,
                                                                                 value)

validation.register(DateValidator('isValidDate'))

