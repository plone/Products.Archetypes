import sys
import os, os.path
import socket
from random import random, randint
from time import time
from inspect import getargs
from md5 import md5
from types import TupleType, ListType, StringType, ClassType, IntType, NoneType
from UserDict import UserDict as BaseDict

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ExtensionClass import ExtensionClass
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.translate import translate

try:
    _v_network = str(socket.gethostbyname(socket.gethostname()))
except:
    _v_network = str(random() * 100000000000000000L)

def make_uuid(*args):
    t = str(time() * 1000L)
    r = str(random()*100000000000000000L)
    data = t +' '+ r +' '+ _v_network +' '+ str(args)
    uid = md5(data).hexdigest()
    return uid

# linux kernel uid generator. It's a little bit slower but a little bit better
KERNEL_UUID = '/proc/sys/kernel/random/uuids'

if os.path.isfile(KERNEL_UUID):
    HAS_KERNEL_UUID = True
    def uuid_gen():
        fp = open(KERNEL_UUID, 'r')
        while 1:
            uid = fp.read()[:-1]
            fp.seek(0)
            yield uid
    uid_gen = uuid_gen()

    def kernel_make_uuid(*args):
        return uid_gen.next()
else:
    HAS_KERNEL_UUID = False
    kernel_make_uuid = make_uuid


def fixSchema(schema):
    """Fix persisted schema from AT < 1.3 (UserDict-based)
    to work with the new fixed order schema."""
    if not hasattr(aq_base(schema), '_fields'):
        fields = schema.data.values()
        from Products.Archetypes.schema import Schemata
        Schemata.__init__(schema, fields)
        del schema.data
    return schema

_marker = []

def mapply(method, *args, **kw):
    m = method
    if hasattr(m, 'im_func'):
        m = m.im_func
    code = m.func_code
    fn_args = getargs(code)
    call_args = list(args)
    if fn_args[1] is not None and fn_args[2] is not None:
        return method(*args, **kw)
    if fn_args[1] is None:
        if len(call_args) > len(fn_args[0]):
            call_args = call_args[:len(fn_args[0])]
    if len(call_args) < len(fn_args[0]):
        for arg in fn_args[0][len(call_args):]:
            value = kw.get(arg, _marker)
            if value is not _marker:
                call_args.append(value)
                del kw[arg]
    if fn_args[2] is not None:
        return method(*call_args, **kw)
    if fn_args[0]:
        return method(*call_args)
    return method()


def className(klass):
    if type(klass) not in [ClassType, ExtensionClass]:
        klass = klass.__class__
    return "%s.%s" % (klass.__module__, klass.__name__)

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
    # taken from ASPN Python Cookbook,
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560

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


def getRelPath(self, ppath):
    """take something with context (self) and a physical path as a
    tuple, return the relative path for the portal"""
    urlTool = getToolByName(self, 'portal_url')
    portal_path = urlTool.getPortalObject().getPhysicalPath()
    ppath = ppath[len(portal_path):]
    return ppath

def getRelURL(self, ppath):
    return '/'.join(getRelPath(self, ppath))

def getPkgInfo(product):
    """Get the __pkginfo__ from a product

    chdir before importing the product
    """
    prd_home = product.__path__[0]
    cur_dir = os.path.abspath(os.curdir)
    os.chdir(prd_home)
    pkg = __import__('%s.__pkginfo__' % product.__name__, product, product,
                      ['__pkginfo__'])
    os.chdir(cur_dir)
    return pkg

def shasattr(obj, attr, acquire=False):
    """Safe has attribute method

    * It's acquisition safe by default because it's removing the acquisition
      wrapper before trying to test for the attribute.

    * It's not using hasattr which might swallow a ZODB ConflictError (actually
      the implementation of hasattr is swallowing all exceptions). Instead of
      using hasattr it's comparing the output of getattr with a special marker
      object.

    XXX the getattr() trick can be removed when Python's hasattr() is fixed to
    catch only AttributeErrors.

    Quoting Shane Hathaway:

    That said, I was surprised to discover that Python 2.3 implements hasattr
    this way (from bltinmodule.c):

            v = PyObject_GetAttr(v, name);
            if (v == NULL) {
                    PyErr_Clear();
                    Py_INCREF(Py_False);
                    return Py_False;
            }
    	Py_DECREF(v);
    	Py_INCREF(Py_True);
    	return Py_True;

    It should not swallow all errors, especially now that descriptors make
    computed attributes quite common.  getattr() only recently started catching
    only AttributeErrors, but apparently hasattr is lagging behind.  I suggest
    the consistency between getattr and hasattr should be fixed in Python, not
    Zope.

    Shane
    """
    if not acquire:
        obj = aq_base(obj)
    return getattr(obj, attr, _marker) is not _marker


WRAPPER = '__at_is_wrapper_method__'
ORIG_NAME = '__at_original_method_name__'
def isWrapperMethod(meth):
    return getattr(meth, WRAPPER, False)

def wrap_method(klass, name, method, pattern='__at_wrapped_%s__'):
    old_method = getattr(klass, name)
    if isWrapperMethod(old_method):
        log('Wrapping already wrapped method at %s.%s' %
            (klass.__name__, name))
    new_name = pattern % name
    setattr(klass, new_name, old_method)
    setattr(method, ORIG_NAME, new_name)
    setattr(method, WRAPPER, True)
    setattr(klass, name, method)

def unwrap_method(klass, name):
    old_method = getattr(klass, name)
    if not isWrapperMethod(old_method):
        raise ValueError, ('Trying to unwrap non-wrapped '
                           'method at %s.%s' % (klass.__name__, name))
    orig_name = getattr(old_method, ORIG_NAME)
    new_method = getattr(klass, orig_name)
    delattr(klass, orig_name)
    setattr(klass, name, new_method)


def _get_position_after(label, options):
    position = 0 
    for item in options:
        if item['label'] != label:
            continue
        position += 1
    return position

def insert_zmi_tab_before(label, new_option, options):
    _options = list(options)
    position = _get_position_after(label, options)
    _options.insert(position-1, new_option)
    return tuple(_options)

def insert_zmi_tab_after(label, new_option, options):
    _options = list(options)
    position = _get_position_after(label, options)
    _options.insert(position, new_option)
    return tuple(_options)
