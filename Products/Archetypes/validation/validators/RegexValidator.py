from Products.Archetypes.interfaces.IValidator import IValidator

import re
from types import StringType

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
