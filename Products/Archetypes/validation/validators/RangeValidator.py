try:
    from Products.Archetypes.validation.interfaces.IValidator import IValidator
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
    from interfaces.IValidator import IValidator
    del sys, os

class RangeValidator:
    __implements__ = IValidator

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kwargs):
        min, max = args[:2]
        assert(min <= max)
        try:
            nval = float(value)
        except ValueError:
            return ("Validation failed(%(name)s): could not convert '%(value)r' to number" %
                    { 'name' : self.name, 'value': value})
        if min <= nval < max:
            return 1

        return ("Validation failed(%(name)s): '%(value)s' out of range(%(min)s, %(max)s)" %
                { 'name' : self.name, 'value': value, 'min' : min, 'max' : max,})
