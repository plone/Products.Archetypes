from validation.interfaces import ivalidator
from DateTime import DateTime
from Registry import registerValidator

class DateValidator:

    __implements__ = (ivalidator,)

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kwargs):
        if not value:
            return ("Validation Failed(%s): value is "
                    "empty or not informed (%s)." % (self.name, repr(value)))
        if not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                return ("Validation Failed(%s): could not "
                        "convert %s to a date.""" % (self.name, value))

registerValidator(DateValidator('isValidDate'))
