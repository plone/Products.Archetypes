import re
from types import StringType
from types import FileType

from Products.Archetypes.interfaces.IValidator import IValidator

from Acquisition import aq_base
from DateTime import DateTime
from ZPublisher.HTTPRequest import FileUpload
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALGenerator import TALGenerator
from Products.PageTemplates.Expressions import getEngine

_marker = object()

# ****************************************************************************

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

# ****************************************************************************

def ignoreRE(value, expression):
    ignore = re.compile(expression)
    return ignore.sub('', value)

class RegexValidator:
    __implements__ = IValidator

    def __init__(self, name, *args, **kw):
        self.name = name
        self.title = kw.get('title', name)
        self.description = kw.get('description', '')
        self.errmsg = kw.get('errmsg', 'fails tests of %s' % name)
        self.regex_strings = args
        self.ignore = kw.get('ignore', None)
        self.regex = []
        self.compileRegex()

    def compileRegex(self):
        for r in self.regex_strings:
            self.regex.append(re.compile(r))        
    
    def __getstate__(self):
        """Because copy.deepcopy and pickle.dump cannot pickle a regex pattern
        I'm using the getstate/setstate hooks to set self.regex to []
        """
        d = self.__dict__.copy()
        d['regex'] = []
        return d
    
    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.compileRegex()

    def __call__(self, value, *args, **kwargs):
        if type(value) != StringType:
            return ("Validation failed(%(name)s): %(value)s of type %(type)s, expected 'string'" %
                    { 'name' : self.name, 'value': value, 'type' : type(value)})

        ignore = kwargs.get('ignore', None)
        if ignore:
            value = ignoreRE(value, ignore)
        elif self.ignore:
            value = ignoreRE(value, self.ignore)


        for r in self.regex:
            m = r.match(value)
            if not m:
                return ("Validation failed(%(name)s): '%(value)s' %(errmsg)s' " % 
                        { 'name' : self.name, 'value': value, 'errmsg' : self.errmsg})
        return 1

# ****************************************************************************

class EmptyValidator:
    __implements__ = IValidator

    def __init__(self, name, title='', description='', showError=True):
        self.name = name
        self.title = title or name
        self.description = description
        self.showError = showError

    def __call__(self, value, *args, **kwargs):
        isEmpty  = kwargs.get('isEmpty', False)
        instance = kwargs.get('instance', None)
        field    = kwargs.get('field', None)

        # XXX: This is a temporary fix. Need to be fixed right for AT 2.0
        #      content_edit / BaseObject.processForm() calls
        #      widget.process_form a second time!
        if instance and field:
            widget  = field.widget
            request = getattr(instance, 'REQUEST', None)
            if request:
                form   = request.form
                result = widget.process_form(instance, field, form,
                                             empty_marker=_marker,
                                             emptyReturnsMarker=True)
                if result is _marker or result is None:
                    isEmpty = True

        if isEmpty:
            return True
        elif value == '' or value is None:
            return True
        else:
            if getattr(self, 'showError', False):
                return ("Validation failed(%(name)s): '%(value)s' is not empty." %
                       { 'name' : self.name, 'value': value})
            else:
                return False

# ****************************************************************************

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

# ****************************************************************************

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

# ****************************************************************************

class TALValidator:
    """Validates a text to be valid TAL code
    """

    __implements__ = IValidator

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kw):
        gen = TALGenerator(getEngine(), xml=1, source_file=None)
        parser = HTMLTALParser(gen)
        try:
            parser.parseString(value)
        except Exception, err:
            return ("Validation Failed(%s): \n %s" % (self.name, err))
        return 1
    
