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
"""
Unittests for a renaming archetypes objects.

$Id$
"""

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase

from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.tests.utils import populateFolder

from Products.Archetypes.tests.utils import wrap_method
from Products.Archetypes.tests.utils import unwrap_method
from Products.Archetypes.utils import shasattr
from Products.Archetypes.atapi import BaseContent
from Products.Archetypes.config import UUID_ATTR

import transaction
import warnings

class Counter:

    def __init__(self):
        self.ids = {}

    def add(self, uid):
        if not self.ids.has_key(uid):
            self.ids[uid] = 0
        self.ids[uid] += 1

    def reset(self):
        self.__init__()

    def get(self, uid):
        if not self.ids.has_key(uid):
            self.ids[uid] = 0
        return self.ids[uid]

ADD_COUNTER = Counter()
DELETE_COUNTER = Counter()
CLONE_COUNTER = Counter()

WARNING_LEVEL = 2
DEBUG_CALL = False

def UID(obj):
    uid = shasattr(obj, UUID_ATTR) and obj.UID() or obj.absolute_url()
    return uid

def manage_afterAdd(self, item, container):
    res = self.__test_manage_afterAdd__(item, container)
    uid = UID(self)
    ADD_COUNTER.add(uid)
    if DEBUG_CALL:
        warnings.warn("manage_afterAdd called: %s:%s" %
                      (uid, ADD_COUNTER.get(uid)),
                      UserWarning,
                      WARNING_LEVEL)
    return res

def manage_beforeDelete(self, item, container):
    uid = UID(self)
    DELETE_COUNTER.add(uid)
    if DEBUG_CALL:
        warnings.warn("manage_beforeDelete called: %s:%s" %
                      (uid, DELETE_COUNTER.get(uid)),
                      UserWarning,
                      WARNING_LEVEL)
    return self.__test_manage_beforeDelete__(item, container)

def manage_afterClone(self, item):
    uid = UID(self)
    CLONE_COUNTER.add(uid)
    if DEBUG_CALL:
        warnings.warn("manage_afterClone called: %s:%s" %
                      (uid, CLONE_COUNTER.get(uid)),
                      UserWarning,
                      WARNING_LEVEL)
    return self.__test_manage_afterClone__(item)

counts = (ADD_COUNTER, DELETE_COUNTER, CLONE_COUNTER)
meths = {'manage_afterAdd':manage_afterAdd,
         'manage_beforeDelete':manage_beforeDelete,
         'manage_afterClone':manage_afterClone
         }

class RenameTests(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        for c in counts:
            c.reset()
        for name, meth in meths.items():
            wrap_method(BaseContent, name, meth, pattern='__test_%s__')

    def beforeTearDown(self):
        ATSiteTestCase.beforeTearDown(self)
        for name in meths.keys():
            unwrap_method(BaseContent, name)

    def test_rename(self):
        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(self.folder, portal_type='Fact', id=obj_id)
        content = 'The book is on the table!'
        doc.setQuote(content, mimetype="text/plain")
        self.failUnless(str(doc.getQuote()) == str(content))
        # make sure we have _p_jar
        transaction.savepoint(optimistic=True)
        self.folder.manage_renameObject(obj_id, new_id)
        doc = getattr(self.folder, new_id)
        self.failUnless(str(doc.getQuote()) == str(content))
        uid = UID(doc)
        # Should call afterAdd twice, one for the object
        # creation and another for the rename
        self.assertEquals(ADD_COUNTER.get(uid), 3)
        # Should call beforeDelete once, when renaming the object
        self.assertEquals(DELETE_COUNTER.get(uid), 1)
        # Should never call afterClone
        self.assertEquals(CLONE_COUNTER.get(uid), 0)

    def getCounts(self, obj):
        uid = UID(obj)
        return (ADD_COUNTER.get(uid),
                DELETE_COUNTER.get(uid),
                CLONE_COUNTER.get(uid))

    def test_recursive(self):
        # Test for recursive calling of manage_after{Add|Clone}
        # and manage_beforeDelete. (bug #905677)
        populateFolder(self.folder, 'SimpleFolder', 'DDocument')
        d = self.folder.folder2.folder22.folder221.doc2211
        uid = UID(d)
        # Called afterAdd once
        self.assertEquals(ADD_COUNTER.get(uid), 2)
        # Never called beforeDelete or afterClone
        self.assertEquals(DELETE_COUNTER.get(uid), 0)
        self.assertEquals(CLONE_COUNTER.get(uid), 0)

        # make sure we have _p_jar
        transaction.savepoint(optimistic=True)

        d_count = self.getCounts(d)

        # Rename the parent folder
        self.folder.folder2.folder22.manage_renameObject('folder221',
                                                         'new_folder221')
        expected = (d_count[0]+1, d_count[1]+1, d_count[2]+0)
        got = self.getCounts(d)
        self.assertEquals(got, expected)

        # Update base count
        d_count = got

        # Rename the root folder
        self.folder.manage_renameObject('folder2', 'new_folder2')

        expected = (d_count[0]+1, d_count[1]+1, d_count[2]+0)
        got = self.getCounts(d)
        self.assertEquals(got, expected)

        # Update base count
        d_count = got

        # Copy the root folder
        cb = self.folder.manage_copyObjects(['new_folder2'])
        self.folder.manage_pasteObjects(cb)

        # Should *not* call manage_afterAdd or manage_afterClone,
        # or to manage_beforeDelete for the source object.
        expected = (d_count[0], d_count[1], d_count[2])
        got = self.getCounts(d)
        self.assertEquals(got, expected)

        new_d = self.folder.copy_of_new_folder2.folder22.new_folder221.doc2211
        got = self.getCounts(new_d)
        # Should have called manage_afterAdd and manage_afterClone for
        # the *new* object.
        self.assertEquals(got, (1, 0, 1))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(RenameTests))
    return suite
