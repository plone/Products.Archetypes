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

from UserDict import DictMixin
from types import StringType, TupleType

from BTrees.OOBTree import OOBTree
from  Persistence import Persistent
from Acquisition import Explicit, aq_base
from AccessControl import ClassSecurityInfo
from ExtensionClass import Base
from Globals import InitializeClass

from Products.Archetypes.interfaces.IAnnotations import IATAnnotations, IATAnnotatable

# annotation keys
AT_ANN_STORAGE = 'Archetypes.storage.AnnotationStorage'
AT_MD_STORAGE  = 'Archetypes.storage.MetadataAnnotationStorage'
AT_FIELD_MD    = 'Archetypes.field.Metadata'
AT_REF         = 'Archetypes.referenceEngine.Reference'


class ATAnnotations(DictMixin, Explicit, Persistent):
    """Store annotations in the '_at_annotations_' attribute on a IATAnnotatable
       object.
    """
    __implements__ = IATAnnotations
    __used_for__ = IATAnnotatable
    
    security = ClassSecurityInfo()
    security.declareObjectPrivate()

    def __init__(self, obj):
        self._obj = obj

    # basic methods required for DictMixin
    
    def __nonzero__(self):
        return bool(getattr(aq_base(self._obj), '_at_annotations_', False))

    def get(self, key, default=None):
        annotations = getattr(aq_base(self._obj), '_at_annotations_', None)
        if not annotations:
            return default

        return annotations.get(key, default)

    def __getitem__(self, key):
        annotations = getattr(aq_base(self._obj), '_at_annotations_', None)
        if annotations is None:
            raise KeyError, key

        return annotations[key]
        
    def keys(self):
        annotations = getattr(aq_base(self._obj), '_at_annotations_', None)
        if annotations is None:
            return []

        return annotations.keys()
    
    def __setitem__(self, key, value):
        if type(key) is not StringType:
            raise TypeError('ATAnnotations key must be a string')
        try:
            # XXX do we need an acquisition context?
            annotations = aq_base(self._obj)._at_annotations_
        except AttributeError:
            annotations = aq_base(self._obj)._at_annotations_ = OOBTree()

        annotations[key] = value
        self._p_changed = 1

    def __delitem__(self, key):
        try:
            annotation = aq_base(self._obj)._at_annotations_
        except AttributeError:
            raise KeyError, key

        del annotation[key]
        self._p_changed = 1
        
    # additional methods
    
    def set(self, key, value):
        self[key] = value
        
    def getSubkey(self, key, default=None, subkeys=()):
        """Get annotations using a key and one or multiple subkeys
        
        For subkeys being a string the value is stored in a key named
        key-subkeys::

            obj.getSubkeys('foo', subkeys='bar')
            obj.get('foo-bar')
            obj._at_annotations_['foo-bar']
            
        For subkeys beeing a tuple with 2 elements the value is stored in an
        OOBTree named key-subkeys[0] using the key subkeys[1] on this
        particular OOBTree::
            
            obj.getSubkeys('foo', subkeys=('ham', 'egg'))
            obj.get('foo-ham')['egg']
            obj._at_annotations_['foo-ham']['egg']
        """
        if isinstance(subkeys, StringType):
            k = '%s-%s' % (key, subkeys)
            return self.get(k, default)
        elif isinstance(subkeys, TupleType):
            if len(subkeys) != 2:
                raise KeyError('Subkeys tuple must have exactly two elements')
            k = '%s-%s' % (key, subkeys[0])
            if not self.has_key(k):
                return default
            else:
                btree = self[k]
                return btree.get(subkeys[1], default)
        else:
            raise TypeError('Invalid subkey type %s, must be string or tuple' % type(subkeys))
    
    def setSubkey(self, key, value, subkeys=()):
        """Stores data using a key and one to multiple subkeys
        """
        if isinstance(subkeys, StringType):
            k = '%s-%s' % (key, subkeys)
            if isinstance(self.get(k, None), OOBTree):
                raise KeyError('Key %s is already in use as OOBTree' % k)
            self[k] = value
        elif isinstance(subkeys, TupleType):
            if len(subkeys) != 2:
                raise KeyError('Subkeys tuple must have exactly two elements')
            k = '%s-%s' % (key, subkeys[0])
            if not self.has_key(k):
                btree = self[k] = OOBTree()
            else:
                btree = self[k]
                if not isinstance(self.get(k, None), OOBTree):
                    raise KeyError('Key %s is already and can\'t be used as OOBTree container' % k)
            btree[subkeys[1]] = value
        else:
            raise TypeError('Invalid subkey type %s, must be string or tuple' % type(subkeys))

        self._p_changed = 1

    def delSubkey(self, key, subkeys=()):
        """Removes a subkey
        """
        if isinstance(subkeys, StringType):
            k = '%s-%s' % (key, subkeys)
            del self[k]
        elif isinstance(subkeys, TupleType):
            if len(subkeys) != 2:
                raise KeyError('Subkeys tuple must have exactly two elements')
            k = '%s-%s' % (key, subkeys[0])
            del self[k][subkeys[1]]
        else:
            raise TypeError('Invalid subkey type %s, must be string or tuple' % type(subkeys))
        self._p_changed = 1

    def hasSubkey(self, key, subkeys=()):
        """
        """
        if isinstance(subkeys, StringType):
            k = '%s-%s' % (key, subkeys)
            return self.has_key(k)
        elif isinstance(subkeys, TupleType):
            if len(subkeys) != 2:
                raise KeyError('Subkeys tuple must have exactly two elements')
            k = '%s-%s' % (key, subkeys[0])
            if not self.has_key(k):
                return False
            else:
                btree = self[k]
                return btree.has_key(subkeys[1])
        else:
            raise TypeError('Invalid subkey type %s, must be string or tuple' % type(subkeys))

    def getObject(self):
        return self._obj

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

class ATAnnotatableMixin(Base):
    __implements__ = IATAnnotatable
    security = ClassSecurityInfo()
    
    security.declarePrivate('getAnnotation')
    def getAnnotation(self):
        """Get an ATAnnotation object for self
        """
        return ATAnnotations(self).__of__(self)
    
    security.declarePrivate('hasAnnotation')
    def hasAnnotation(self):
        """Check if the object has annotations
        """
        return bool(self.getAnnotation())

InitializeClass(ATAnnotatableMixin)

