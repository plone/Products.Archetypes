# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""Module with misc useful utility methods for Archetypes
"""

import sys
import os, os.path
import socket
from random import random, randint
from time import time
from inspect import getargs
from md5 import md5
from types import ClassType
from UserDict import UserDict as BaseDict

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ExtensionClass import ExtensionClass
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import KERNEL_UUID
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.translate import translate
from Products.Archetypes.interfaces.base import IBaseObject

from Interface.Implements import getImplementsOfInstances
from Interface.Implements import flattenInterfaces
from Interface import Interface

_marker = []

try:
    _v_network = str(socket.gethostbyname(socket.gethostname()))
except:
    _v_network = str(random() * 100000000000000000L)

def make_uuid(*args):
    """Generate a universal unique id
    
    The make_uuid methods generates a unique id using the following data:
        * the current time
        * a random value
        * the hostname of the server (or if not available more random data)
        * additional arguments converted to a string

    The random data is converted to a MD5 hexdigest
    """
    t = str(time() * 1000L)
    r = str(random()*100000000000000000L)
    data = t +' '+ r +' '+ _v_network +' '+ str(args)
    uid = md5(data).hexdigest()
    return uid

# linux kernel uid generator. It's a little bit slower but a little bit better
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
        """Linux kernel based uuid generator using %s
        """ % KERNEL_UUID
        return uid_gen.next()
else:
    HAS_KERNEL_UUID = False
    def kernel_make_uuid(*args):
        """Fallback kernel uuid generator
        
        Using the standard make_uuid method because %s wasn't available on this
        system
        """ % KERNEL_UUID
        return make_uuid(*args)

def fixSchema(schema):
    """Fix persisted schema from AT < 1.3 (UserDict-based)
    to work with the new fixed order schema."""
    if not hasattr(aq_base(schema), '_fields'):
        fields = schema.data.values()
        from Products.Archetypes.schema import Schemata
        Schemata.__init__(schema, fields)
        del schema.data
    return schema

def mapply(method, *args, **kw):
    """Magic apply method
    
    XXX explain me :)
    """
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
    """Returns the dotted path to an object's clsas
    """
    if type(klass) not in [ClassType, ExtensionClass]:
        klass = klass.__class__
    return "%s.%s" % (klass.__module__, klass.__name__)

def getDottedName(obj):
    """XXX
    """
    try:
        return "%s.%s" % (obj.__module__, obj.__name__)
    except AttributeError:
        return className(obj)

def getDoc(klass):
    """Return the doc string of an object

    Or an empty string if the object doesn't have a doc string

    >>> getDoc(getDoc).startswith("Return the doc string of an object")
    True
    """
    return klass.__doc__ or ''

def getBaseClasses(class_):
    """Get a list of super classes
    
    XXX Is it truely the right resolution order for old style classes?
    
    >>> from Products.Archetypes.base import BaseObject
    >>> bases = getBaseClasses(BaseObject)
    >>> base_names = [getDottedName(class_) for class_ in bases]
    >>> base_names
    ['Products.Archetypes.refengine.referenceable.Referenceable',
    'OFS.CopySupport.CopySource',
    'Products.Archetypes.lib.annotations.ATAnnotatableMixin',
    'ExtensionClass.Base']
    """
    result = []
    _flatten(class_, result)
    # remove double doubled entries from back to front
    #result.reverse()
    result = unique(result)
    #result.reverse()
    return result

def _flatten(class_, result):
    """Flattens a class tree

    >>> from Products.Archetypes.base import BaseObject
    >>> bases = _flatten(BaseObject, [])
    >>> base_names = [getDottedName(class_) for class_ in bases]
    >>> base_names
    ['Products.Archetypes.refengine.referenceable.Referenceable',
    'OFS.CopySupport.CopySource', 'ExtensionClass.Base',
    'Products.Archetypes.lib.annotations.ATAnnotatableMixin',
    'ExtensionClass.Base']
    """

    for base in class_.__bases__:
        result.append(base)
        _flatten(base, result)
    return result

def getInterfaces(class_):
    """Get a list of all interfaces which are implemented by a class

    >>> from Products.Archetypes.base import BaseObject
    >>> interfaces = getInterfaces(BaseObject)
    >>> interface_names = [getDottedName(interface) for interface in interfaces]
    >>> interface_names.sort()
    >>> interface_names
    ['Products.Archetypes.interfaces.annotations.IATAnnotatable',
    'Products.Archetypes.interfaces.base.IBaseObject',
    'Products.Archetypes.interfaces.referenceable.IReferenceable']
    """
    interfaces = getImplementsOfInstances(class_)
    if not isinstance(interfaces, tuple):
        interfaces = (interfaces,)
    if interfaces:
        interfaces = flattenInterfaces(interfaces)
        interfaces = unique(interfaces)
        if Interface in interfaces:
            interfaces.remove(Interface)
        return interfaces
    else:
        return ()

def findBaseTypes(klass):
    """XXX
    """
    bases = []
    if hasattr(klass, '__bases__'):
        for b in klass.__bases__:
            if IBaseObject.isImplementedByInstancesOf(b):
                bases.append(className(b))
    return bases

def capitalize(s):
    """Capitalize the first letter of a string
    
    >>> capitalize('foo')
    'Foo'
    >>> capitalize('Foo')
    'Foo'
    """
    if s[0].islower():
        s = s[0].upper() + s[1:]
    return s

def findDict(listofDicts, key, value):
    """Look at a list of dicts for one where key == value
    
    >>> d1 = {'foo'  : 'bar'}
    >>> d2 = {'egg'  : 'spam'}
    >>> d3 = {'here' : 'there'}
    
    >>> findDict((d1, d2, d3), 'foo', 'bar') is d1
    True
    >>> findDict((d1, d2, d3), 'egg', 'spam') is d2
    True
    >>> findDict((d1, d2, d3), 'foo', 'spam') is None
    True
    """
    for d in listofDicts:
        if d.has_key(key):
            if d[key] == value:
                return d
    return None

def basename(path):
    """XXX
    """
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
    """Calculate the relative path to the root of the portal
    
    Take something with context (self) and a physical path as a
    tuple, return the relative path for the portal
    
    >>> portal.getPhysicalPath()
    ('', 'cmf')
    >>> itemPhysicalPath = ('', 'cmf', 'folder', 'item')
    >>> getRelPath(portal, itemPhysicalPath)
    ('folder', 'item')
    """
    urlTool = getToolByName(self, 'portal_url')
    portal_path = urlTool.getPortalObject().getPhysicalPath()
    ppath = ppath[len(portal_path):]
    return ppath

def getRelURL(self, ppath):
    """Calculate the relative url to the root of the portal
    
    >>> portal.getPhysicalPath()
    ('', 'cmf')
    >>> itemPhysicalPath = ('', 'cmf', 'folder', 'item')
    >>> getRelURL(portal, itemPhysicalPath)
    'folder/item'
    """
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

##def _get_position_after(label, options):
##    position = 0
##    for item in options:
##        if item['label'] != label:
##            continue
##        position += 1
##    return position
##
##def insert_zmi_tab_before(label, new_option, options):
##    _options = list(options)
##    position = _get_position_after(label, options)
##    _options.insert(position-1, new_option)
##    return tuple(_options)
##
##def insert_zmi_tab_after(label, new_option, options):
##    _options = list(options)
##    position = _get_position_after(label, options)
##    _options.insert(position, new_option)
##    return tuple(_options)
