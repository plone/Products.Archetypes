# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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

import sys
import os, os.path
import socket
from random import random, randint
from time import time
from inspect import getargs
from md5 import md5
from types import TupleType, ListType, ClassType, IntType, NoneType
from types import UnicodeType, StringType
from UserDict import UserDict as BaseDict

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ExtensionClass import ExtensionClass
from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.translate import translate

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
        if type(key) not in (StringType, UnicodeType, IntType):
            raise TypeError('DisplayList keys must be strings or ints, got %s' %
                            type(key))
        if type(msgid) not in (StringType, NoneType):
            raise TypeError('DisplayList msg ids must be strings, got %s' %
                            type(msgid))
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
        for k, v in self._values.items():
            if repr(value) == repr(k):
                return v[1]
        return default

    def getValue(self, key, default=None):
        "get value"
        if type(key) not in (StringType, UnicodeType, IntType):
            raise TypeError('DisplayList keys must be strings or ints, got %s' %
                            type(key))
        v = self._keys.get(key, None)
        if v: return v[1]
        for k, v in self._keys.items():
            if repr(key) == repr(k):
                return v[1]
        return default

    def getMsgId(self, key):
        "get i18n msgid"
        if type(key) is not StringType:
            raise TypeError('DisplayList keys must be strings or ints, got %s' %
                            type(key))
        if self._i18n_msgids.has_key(key):
            return self._i18n_msgids[key]
        else:
            return self._keys[key][1]

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
        """return a new display list sorted by key"""
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

class Vocabulary(DisplayList):
    """
    Wrap DisplayList class and add internationalisation
    """

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, display_list, instance, i18n_domain):
        self._keys = display_list._keys
        self._i18n_msgids = display_list._i18n_msgids
        self._values = display_list._values
        self._itor   = display_list._itor
        self.index = display_list.index
        self._instance = instance
        self._i18n_domain = i18n_domain

    def getValue(self, key, default=None):
        """
        Get i18n value
        """
        if type(key) not in (StringType, UnicodeType, IntType):
            raise TypeError('DisplayList keys must be strings or ints, got %s' %
                            type(key))
        v = self._keys.get(key, None)
        value = default
        if v:
            value = v[1]
        else:
            for k, v in self._keys.items():
                if repr(key) == repr(k):
                    value = v[1]
                    break

        if self._i18n_domain and self._instance:
            msg = self._i18n_msgids.get(key, None) or value

            return translate(self._i18n_domain, msg,
                                  context=self._instance, default=value)
        else:
            return value

InitializeClass(Vocabulary)

class OrderedDict(BaseDict):
    """A wrapper around dictionary objects that provides an ordering for
       keys() and items()."""

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, dict=None):
        BaseDict.__init__(self, dict)
        if dict is not None:
            self._keys = self.data.keys()
        else:
            self._keys = []

    def __setitem__(self, key, item):
        if not self.data.has_key(key):
            self._keys.append(key)
        return BaseDict.__setitem__(self, key, item)

    def __delitem__(self, key):
        BaseDict.__delitem__(self, key)
        self._keys.remove(key)

    def clear(self):
        BaseDict.clear(self)
        self._keys = []

    def keys(self):
        return self._keys

    def items(self):
        return [(k, self.get(k)) for k in self._keys]

    def reverse(self):
        items = list(self.items())
        items.reverse()
        return items

    def values(self):
        return [self.get(k) for k in self._keys]

    def update(self, dict):
        for k in dict.keys():
            if not self.data.has_key(k):
                self._keys.append(k)
        return BaseDict.update(self, dict)

    def setdefault(self, key, failobj=None):
        if not self.data.has_key(key):
            self._keys.append(key)
        return BaseDict.setdefault(self, key, failobj)

    def popitem(self):
        if not self.data:
            raise KeyError, 'dictionary is empty'
        k = self._keys.pop()
        v = self.data.get(k)
        del self.data[k]
        return (k, v)

InitializeClass(OrderedDict)

