try:
    from Products.Archetypes.validation.interfaces.IValidator import IValidator
    from Acquisition import aq_base
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
    from interfaces.IValidator import IValidator
    del sys, os

_marker = []

try:
    True
except NameError:
    True=1
    False=0

from types import FileType
try:
    from ZPublisher.HTTPRequest import FileUpload
except ImportError:
    FileUpload = FileType

class MaxSizeValidator:
    """Tests if an upload, file or something supporting len() is smaller than a 
       given max size value
       
    If it's a upload or file like thing it is using seek(0, 2) which means go
    to the end of the file and tell() to get the size in bytes otherwise it is
    trying to use len()
    
    The maxsize can be acquired from the kwargs in a call, a 
    getMaxSizeFor(fieldname) on the instance, a maxsize attribute on the field
    or a given maxsize at validator initialization.
    """
    __implements__ = IValidator

    def __init__(self, name, title='', description='', maxsize=0):
        self.name = name
        self.title = title or name
        self.description = description
        self.maxsize= maxsize

    def __call__(self, value, *args, **kwargs):
        instance = kwargs.get('instance', None)
        field    = kwargs.get('field', None)

        # get max size
        if kwargs.has_key('maxsize'):
            maxsize = kwargs.get('maxsize')
        elif hasattr(aq_base(instance), 'getMaxSizeFor'):
            maxsize = instance.getMaxSizeFor(field.getName())
        elif hasattr(field, 'maxsize'):
            maxsize = field.maxsize
        else:
            # set to given default value (default defaults to 0)
            maxsize = self.maxsize
        
        if not maxsize:
            return True
        
        # calculate size
        elif isinstance(value, FileUpload) or type(value) is FileType \
          or hasattr(aq_base(value), 'tell'):
            value.seek(0, 2) # eof
            size = value.tell()
            value.seek(0)
        else:
            try:
                size = len(value)
            except TypeError:
                size = 0
        size = float(size)
        sizeMB = (size / (1024 * 1024))

        if sizeMB > maxsize:
            return ("Validation failed(%(name)s: Uploaded data is too large: %(size).3fMB (max %(max)fMB)" %
                     { 'name' : self.name, 'size' : sizeMB, 'max' : maxsize })
        else:
            return True


try:
    from DateTime import DateTime
except ImportError:
    # XXX use python datetime?
    DateTime = lambda date: None

class DateValidator:

    __implements__ = IValidator

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kwargs):
        if not value:
            return ("Validation failed(%s): value is "
                    "empty (%s)." % (self.name, repr(value)))
        if not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                return ("Validation failed(%s): could not "
                        "convert %s to a date.""" % (self.name, value))
        return True


validatorList = [
    MaxSizeValidator('isMaxSize', title='', description=''),
    DateValidator('isValidDate', title='', description=''),
    ]

__all__ = ('validatorList', )

