from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils import _verifyActionPermissions, getToolByName
from types import TupleType, ListType
from debug import log
import sys
import os.path

def productDir():
    module = sys.modules[__name__]
    return os.path.dirname(module.__file__)

def pathFor(path=None, file=None):
    base = productDir()
    if path:
        base = os.path.join(base, path)
    if file:
        base = os.path.join(base, file)

    return base

def capitalize(string):
    if string[0].islower():
        string = string[0].upper() + string[1:]
    return string

def findDict(listofDicts, key, value):
    #Look at a list of dicts for one where key == value
    for d in listofDicts:
        if d.has_key(key):
            if d[key] == value:
                return d
    return None


def basename(path):
    return path[max(path.rfind('\\'), path.rfind('/'))+1:]

def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """
    # taken from ASPN Python Cookbook, http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

class DisplayList:
    """Static display lists, can look up on
    either side of the dict, and get them in sorted order
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, data=None):
        self._keys = {}
        self._i18n_msgids = {}
        self._values = {}
        self._itor   = []
        self.index = 0
        if data:
            self.fromList(data)

    def __repr__(self):
        return '<DisplayList %s at %s>' % (self[:], id(self))

    def __str__(self):
        return str(self[:])

    def __call__(self):
        return self

    def fromList(self, lst):
        for item in lst:
            if isinstance(item, ListType):
                item = tuple(item)
            self.add(*item)

    def __len__(self):
        return self.index

    def __add__(self, other):
        a = tuple(self.items())
        if hasattr(other, 'items'):
            b = other.items()
        else: #assume a seq
            b = tuple(zip(other, other))

        msgids = self._i18n_msgids
        msgids.update(getattr(other, '_i18n_msgids', {}))

        v = DisplayList(a + b)
        v._i18n_msgids = msgids
        return v

    def index_sort(self, a, b):
        return  a[0] - b[0]

    def add(self, key, value, msgid=None):
        self.index +=1
        k = (self.index, key)
        v = (self.index, value)

        self._keys[key] = v
        self._values[value] = k
        self._itor.append(key)
        if msgid: self._i18n_msgids[key] = msgid

    def getKey(self, value, default=None):
        """get key"""
        v = self._values.get(value, None)
        if v: return v[1]
        return default

    def getValue(self, key, default=None):
        "get value"
        v = self._keys.get(key, None)
        if v: return v[1]
        return default

    def getMsgId(self, key):
        "get i18n msgid"
        try:
            return self._i18n_msgids[key]
        except (KeyError, AttributeError):
            return self._keys[key]

    def keys(self):
        "keys"
        kl = self._values.values()
        kl.sort(self.index_sort)
        return [k[1] for k in kl]

    def values(self):
        "values"
        vl = self._keys.values()
        vl.sort(self.index_sort)
        return [v[1] for v in vl]

    def items(self):
        """items"""
        keys = self.keys()
        return tuple([(key, self.getValue(key)) for key in keys])

    def sortedByValue(self):
        """return a new display list sorted by value"""
        def _cmp(a, b):
            return cmp(a[1], b[1])
        values = list(self.items())
        values.sort(_cmp)
        return DisplayList(values)

    def sortedByKey(self):
        """return a new display list sorted by value"""
        def _cmp(a, b):
            return cmp(a[0], b[0])
        values = list(self.items())
        values.sort(_cmp)
        return DisplayList(values)

    def __cmp__(self, dest):
        if not isinstance(dest, DisplayList):
            raise TypeError, 'Cant compare DisplayList to %s' % (type(dest))

        return cmp(self.sortedByKey()[:], dest.sortedByKey()[:])

    def __getitem__(self, key):
        #Ok, this is going to pass a number
        #which is index but not easy to get at
        #with the data-struct, fix when we get real
        #itor/generators
        return self._itor[key]

    def __getslice__(self,i1,i2):
        r=[]
        for i in xrange(i1,i2):
            try: r.append((self._itor[i], self.getValue(self._itor[i]),))
            except IndexError: return r
        return DisplayList(r)

    slice=__getslice__

InitializeClass(DisplayList)
