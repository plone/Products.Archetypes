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

from UserDict import DictMixin

from BTrees.OOBTree import OOBTree
from Acquisition import Explicit
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.Archetypes.interfaces.annotations import IATAnnotations
from Products.Archetypes.interfaces.annotations import IATAnnotatable

from zope.interface import implements
from zope.component import adapts

# annotation keys
AT_ANN_STORAGE = 'Archetypes.storage.AnnotationStorage'
AT_MD_STORAGE  = 'Archetypes.storage.MetadataAnnotationStorage'
AT_FIELD_MD    = 'Archetypes.field.Metadata'
AT_REF         = 'Archetypes.referenceEngine.Reference'

# all keys so someone can test against this list
AT_ANN_KEYS = (AT_ANN_STORAGE, AT_MD_STORAGE, AT_FIELD_MD, AT_REF)

class ATAnnotations(DictMixin, Explicit):
    """Store annotations in the '__annotations__' attribute on a IATAnnotatable
       object.
    """
    implements(IATAnnotations)
    adapts(IATAnnotatable)

    security = ClassSecurityInfo()
    security.declareObjectPrivate()

    def __init__(self, obj):
        self._obj = aq_base(obj)

    # basic methods required for DictMixin

    def __nonzero__(self):
        return bool(getattr(self._obj, '__annotations__', False))

    def get(self, key, default=None):
        annotations = getattr(self._obj, '__annotations__', None)
        if not annotations:
            return default

        return annotations.get(key, default)

    def __getitem__(self, key):
        annotations = getattr(self._obj, '__annotations__', None)
        if annotations is None:
            raise KeyError, key

        return annotations[key]

    def keys(self):
        annotations = getattr(self._obj, '__annotations__', None)
        if annotations is None:
            return []

        return annotations.keys()

    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise TypeError('ATAnnotations key must be a string')
        try:
            annotations = self._obj.__annotations__
        except AttributeError:
            annotations = self._obj.__annotations__ = OOBTree()

        annotations[key] = value

    def __delitem__(self, key):
        try:
            annotation = self._obj.__annotations__
        except AttributeError:
            raise KeyError, key

        del annotation[key]

    # additional methods

    def set(self, key, value):
        self[key] = value

    def getSubkey(self, key, subkey, default=None):
        """Get annotations using a key and onesubkey
        """
        if isinstance(subkey, basestring):
            k = '%s-%s' % (key, subkey)
            return self.get(k, default)
        else:
            raise TypeError('Invalid subkey type %s, must be string type' % type(subkey))

    def setSubkey(self, key, value, subkey):
        """Stores data using a key and one subkey
        """
        if isinstance(subkey, basestring):
            k = '%s-%s' % (key, subkey)
            self[k] = value
        else:
            raise TypeError('Invalid subkey type %s, must be string type' % type(subkey))

    def delSubkey(self, key, subkey):
        """Removes a subkey
        """
        if isinstance(subkey, basestring):
            k = '%s-%s' % (key, subkey)
            del self[k]
        else:
            raise TypeError('Invalid subkey type %s, must be string type' % type(subkey))

    def hasSubkey(self, key, subkey):
        """Checks for the existence of a sub key
        """
        if isinstance(subkey, basestring):
            k = '%s-%s' % (key, subkey)
            return self.has_key(k)
        else:
            raise TypeError('Invalid subkey type %s, must be string type' % type(subkey))

    def getObject(self):
        return self._obj

    def getAnnotationObject(self):
        try:
            return self._obj.__annotations__
        except AttributeError:
            return None

    # DictMixin does define the following methods:
    #def __iter__(self):
    #def has_key(self, key):
    #def __contains__(self, key):
    #def iteritems(self):
    #def iterkeys(self):
    #def itervalues(self):
    #def values(self):
    #def items(self):
    #def clear(self):
    #def setdefault(self, key, default):
    #def pop(self, key, *args):
    #def popitem(self):
    #def update(self, other):
    #def get(self, key, default=None):
    #def __repr__(self):
    #def __cmp__(self, other):
    #def __len__(self):

InitializeClass(ATAnnotations)

def getAnnotation(obj):
     """Get an ATAnnotation object for obj
     """
     return ATAnnotations(obj).__of__(obj)

