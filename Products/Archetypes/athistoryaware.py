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
"""Archetypes history awareness"""
__author__  = 'Martijn Pieters <mj@zopatista.com>'

import itertools

from DateTime import DateTime
from OFS.History import HystoryJar
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from App.class_init import InitializeClass

from AccessControl import ClassSecurityInfo

from annotations import AT_ANN_KEYS
from interfaces.athistoryaware import IATHistoryAware
from zope.interface import implements

# A note about this implementation
#
# Archetypes now stores field data in a __annotations__ BTree, and many (if not
# all) of these field data objects are persistent themselves. This means that
# each of these objects will get it's own revisions in the ZODB, and retrieving
# an object's historic revision will not retrieve historic revisions of
# subobjects.
#
# The following implementation will merge the histories for the main object,
# the __annotations__ BTree, and any persistent annotition that uses an
# Archetypes key. It does not recurse into those objects though (which would
# make the implementation far more complex), so fields like File and Image will
# not be correctly reconstructed.
#
# When an edit is made to an archetype, it may be that only one field is
# altered and only that field is then recorded in a transaction. Adding or
# removing a field from the annotations will result in a new revision of the
# __annotations__ BTree, but the main object remains unaffected. Editing a
# title will affect self, and no fields stored in annotations are altered.
#
# The following table illustrates a series of such transactions
# (__annotations__ is shortened to 'ann', crosses mark comitted revisions,
# a slash marks a removed object):
#
#  tid | self | ann | fld1 | fld2 | fld3 |
# ---------------------------------------------------------------------
#   1  |  x   |  x  |  x   |  x   |      |  Object created
#   2  |  x   |     |  x   |      |      |  Field 1 and title edited
#   3  |      |  x  |      |      |  x   | Field 3 added
#   4  |      |  x  |      |  x   |  /   |  Field 2 edited, field 3 removed
#   5  |  x   |     |  x   |      |      |  More edits
#
# Now, to construct the last 3 historic revisions, one has to pull together
# various object revisions. For tid 5, to construct the full object, one has to
# take tid 4 for __annotations__ and field 2, and no revision for field 3.
# Tid 3 combines tid 2 for self and field 1, tid 1 for field 2 with tid 3
# versions of __annotations__ and field 3.
#
# Note that packing does not remove older revisions still referenced through
# backpointers from not-packed revisions. So, if a pack takes place removing
# items from before tid 4, the revisions for self and field 1 at tid 2, and
# field 2 at tid 1 are still retained. Field 3 will be completely purged, as
# are the revisions for __annotations__ from tids 1 and 3.

# The OFS.History.historicalRevision method fails for OOBTrees.
def _historicalRevision(self, tid):
    state = self._p_jar.oldstate(self, tid)
    try:
        rev = self.__class__.__basicnew__()
    except AttributeError:
        rev = self.__class__()
    rev._p_jar = HystoryJar(self._p_jar)
    rev._p_oid = self._p_oid
    rev._p_serial = tid
    rev.__setstate__(state)
    rev._p_changed = 0
    return rev

def _objectRevisions(obj, limit=10):
    """Iterate over (thread id, persistent object revisions), up to limit"""
    for rev in obj._p_jar.db().history(obj._p_oid, size=limit):
        tid = rev.get('tid', None) or rev.get('serial', None)
        if not tid: # Apparently not all storages provide this?
            return
        # Set 'tid' so we don't have to test for 'serial' again
        rev['tid'] = tid
        rev['object'] = _historicalRevision(obj, tid)
        yield tid, rev

class ATHistoryAwareMixin:
    """Archetypes history aware mixin class

    Provide ZODB revisions, constructed from older transactions. Note that
    these transactions are available only up to the last pack.

    """

    implements(IATHistoryAware)

    security       = ClassSecurityInfo()


    security.declarePrivate('_constructAnnotatedHistory')
    def _constructAnnotatedHistory(self, max=10):
        """Reconstruct historical revisions of archetypes objects

        Merges revisions to self with revisions to archetypes-related items
        in __annotations__. Yields at most max recent revisions.

        """
        # All relevant historical states by transaction id
        # For every tid, keep a dict with object revisions, keyed on annotation
        # id, or None for self and '__annotations__' for the ann OOBTree
        # Initialize with self revisions
        history = dict([(tid, {None: rev})
                        for (tid, rev) in _objectRevisions(self, max)])

        if not getattr(self, '__annotations__', None):
            # No annotations, just return the history we have for self
            # Note that if this object had __annotations__ in a past
            # transaction they will be ignored! Working around this is a
            # YAGNI I think though.
            for tid in sorted(history.keys()):
                yield history[tid][None]
            return

        # Now find all __annotation__ revisions, and the annotation keys
        # used in those.
        annotation_key_objects = {}
        isatkey = lambda k, aak=AT_ANN_KEYS: filter(k.startswith, aak)
        # Loop over max revisions of the __annotations__ object to retrieve
        # all keys (and more importantly, their objects so we can get revisions)
        for tid, rev in _objectRevisions(self.__annotations__, max):
            history.setdefault(tid, {})['__annotations__'] = rev
            revision = rev['object']
            for key in itertools.ifilter(isatkey, revision.iterkeys()):
                if not hasattr(revision[key], '_p_jar'):
                    continue # Not persistent
                if key not in annotation_key_objects:
                    annotation_key_objects[key] = revision[key]

        # For all annotation keys, get their revisions
        for key, obj in annotation_key_objects.iteritems():
            for tid, rev in _objectRevisions(obj, max):
                history.setdefault(tid, {})[key] = rev
        del annotation_key_objects

        # Now we merge the annotation and object revisions into one for each
        # transaction id, and yield the results
        tids = sorted(history.iterkeys(), reverse=True)
        def find_revision(tids, key):
            """First revision of key in a series of tids"""
            has_revision = lambda t, h=history, k=key: k in h[t]
            next_tid = itertools.ifilter(has_revision, tids).next()
            return history[next_tid][key]

        for i, tid in enumerate(tids[:max]):
            revision = find_revision(tids[i:], None)
            obj = revision['object']
            # Track size to maintain correct metadata
            size = revision['size']

            anns_rev = find_revision(tids[i:], '__annotations__')
            size += anns_rev['size']
            anns = anns_rev['object']

            # We use a temporary OOBTree to avoid _p_jar complaints from the
            # transaction machinery
            tempbtree = OOBTree()
            tempbtree.__setstate__(anns.__getstate__())

            # Find annotation revisions and insert
            for key in itertools.ifilter(isatkey, tempbtree.iterkeys()):
                if not hasattr(tempbtree[key], '_p_jar'):
                    continue # Not persistent
                value_rev = find_revision(tids[i:], key)
                size += value_rev['size']
                tempbtree[key] = value_rev['object']

            # Now transfer the tembtree state over to anns, effectively
            # bypassing the transaction registry while maintaining BTree
            # integrity
            anns.__setstate__(tempbtree.__getstate__())
            anns._p_changed = 0
            del tempbtree

            # Do a similar hack to set anns on the main object
            state = obj.__getstate__()
            state['__annotations__'] = anns
            obj.__setstate__(state)
            obj._p_changed = 0

            # Update revision metadata if needed
            if revision['tid'] != tid:
                # any other revision will do; only size and object are unique
                revision = history[tid].values()[0].copy()
                revision['object'] = obj

            # Correct size based on merged records
            revision['size'] = size

            # clean up as we go
            del history[tid]

            yield revision

    security.declarePrivate('getHistories')
    def getHistories(self, max=10):
        """Iterate over historic revisions.

        Yields (object, time, transaction_note, user) tuples, where object
        is an object revision approximating what was committed at that time,
        with the current acquisition context.

        Object revisions include correct archetype-related annotation revisions
        (in __annotations__); other persistent sub-objects are in their current
        revision, not historical!

        """

        parent = aq_parent(self)
        for revision in self._constructAnnotatedHistory(max):
            obj = revision['object'].__of__(parent)
            yield (obj, DateTime(revision['time']), revision['description'],
                   revision['user_name'])

InitializeClass(ATHistoryAwareMixin)
