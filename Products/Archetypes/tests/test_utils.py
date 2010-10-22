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
"""


from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import make_uuid

class UidGeneratorTest(ATTestCase):
    """Some ppl have reported problems with uids. This test isn't mathematical
    correct but should show the issue on plattform. I suspect it's Windows :|
    """

    def test_uuid(self):
        uids = {}
        loop_length = 10**5 # about 1.5 seconds on a fast cpu
        for i in xrange(loop_length):
            uid = make_uuid()
            uids[uid] = 1
        self.failUnlessEqual(len(uids), loop_length)

class DisplayListTest(ATTestCase):

    def test_cmp(self):
        ta = ('a', 'b', 'c')
        tb = ('a', 'c', 'b')
        tc = ('a', 'c', 'c')
        td = ('c', 'b', 'a')
        self.failUnless(DisplayList(zip(ta, ta)) == DisplayList(zip(ta, ta)))
        self.failIf(DisplayList(zip(ta, ta)) == DisplayList(zip(ta, tb)))
        self.failUnless(DisplayList(zip(ta, ta)) == DisplayList(zip(td, td)))
        self.failUnless(DisplayList(zip(tb, ta)) == DisplayList(zip(tb, ta)))
        self.assertRaises(TypeError, cmp, DisplayList(), '')

    def test_slice(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        sub = l[1:]
        self.failUnless(DisplayList(l)[1:] == sub)

    def test_item(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        for i in range(0,2):
            item = ta[i]
            self.failUnless(DisplayList(l)[i] == item)

    def test_add(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)[:]
        self.failUnless(dl == l)
        l.append(('d', 'd'))
        dl.append(('d', 'd'))
        self.failUnless(dl == l)

    def test_len(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(len(dl) == len(l))

    def test_keys(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(tuple(dl.keys()) == ta)

    def test_values(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(tuple(dl.values()) == ta)

    def test_items(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(dl.items() == tuple(l))

    def test_repr(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(repr(dl).find(str(l)))

    def test_str(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(str(dl) == str(l))

    def test_call(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.failUnless(dl == dl)
        self.failUnless(dl() == dl())
        self.failUnless(dl[:] == l)
        self.failUnless(dl()[:] == l)

    def test_sort(self):
        a = (('a','a',), ('b','b'), ('c', 'c'))
        b = (('z','Z',), ('y','Y'), ('x', 'X'))
        c = (('a','Z',), ('c','Y'), ('b', 'X'))
        dla = DisplayList(a)
        dlb = DisplayList(b)
        dlc = DisplayList(c)

        assert dla.values() == ['a', 'b', 'c']
        dlb_s = dlb.sortedByValue()
        assert dlb_s.values() == ['X', 'Y', 'Z']
        dlc_s = dlc.sortedByKey()
        assert dlc_s.values() == ['Z', 'X', 'Y']


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(DisplayListTest))
    suite.addTest(makeSuite(UidGeneratorTest))
    return suite
