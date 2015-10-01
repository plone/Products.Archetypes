# -*- coding: utf-8 -*-
##########################################################################
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
##########################################################################
"""
"""


from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import IntDisplayList
from Products.Archetypes.utils import Vocabulary
from Products.Archetypes.utils import make_uuid


class UidGeneratorTest(ATTestCase):
    """Some ppl have reported problems with uids. This test isn't mathematical
    correct but should show the issue on plattform. I suspect it's Windows :|
    """

    def test_uuid(self):
        uids = {}
        loop_length = 10 ** 5  # about 1.5 seconds on a fast cpu
        for i in xrange(loop_length):
            uid = make_uuid()
            uids[uid] = 1
        self.assertEqual(len(uids), loop_length)


class DisplayListTest(ATTestCase):

    def test_cmp(self):
        ta = ('a', 'b', 'c')
        tb = ('a', 'c', 'b')
        td = ('c', 'b', 'a')
        self.assertTrue(DisplayList(zip(ta, ta)) == DisplayList(zip(ta, ta)))
        self.assertFalse(DisplayList(zip(ta, ta)) == DisplayList(zip(ta, tb)))
        self.assertTrue(DisplayList(zip(ta, ta)) == DisplayList(zip(td, td)))
        self.assertTrue(DisplayList(zip(tb, ta)) == DisplayList(zip(tb, ta)))
        self.assertRaises(TypeError, cmp, DisplayList(), '')

    def test_slice(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        sub = l[1:]
        self.assertTrue(DisplayList(l)[1:] == sub)

    def test_item(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        for i in range(0, 2):
            item = ta[i]
            self.assertTrue(DisplayList(l)[i] == item)

    def test_add(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)[:]
        self.assertTrue(dl == l)
        l.append(('d', 'd'))
        dl.append(('d', 'd'))
        self.assertTrue(dl == l)

    def test_len(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(len(dl) == len(l))

    def test_keys(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(tuple(dl.keys()) == ta)

    def test_values(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(tuple(dl.values()) == ta)

    def test_items(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(dl.items() == tuple(l))

    def test_repr(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(repr(dl).find(str(l)))

    def test_str(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(str(dl) == str(l))

    def test_call(self):
        ta = ('a', 'b', 'c')
        l = zip(ta, ta)
        dl = DisplayList(l)
        self.assertTrue(dl == dl)
        self.assertTrue(dl() == dl())
        self.assertTrue(dl[:] == l)
        self.assertTrue(dl()[:] == l)

    def test_sort(self):
        a = (('a', 'a',), ('b', 'b'), ('c', 'c'))
        b = (('z', 'Z',), ('y', 'Y'), ('x', 'X'))
        c = (('a', 'Z',), ('c', 'Y'), ('b', 'X'))
        dla = DisplayList(a)
        dlb = DisplayList(b)
        dlc = DisplayList(c)

        assert dla.values() == ['a', 'b', 'c']
        dlb_s = dlb.sortedByValue()
        assert dlb_s.values() == ['X', 'Y', 'Z']
        dlc_s = dlc.sortedByKey()
        assert dlc_s.values() == ['Z', 'X', 'Y']

    def test_getValue(self):
        a = (('a', 'A',), ('b', '\xc3\xab'), ('c', u'xeb'), ('d', 42))
        dla = DisplayList(a)
        self.assertEqual(dla.getValue('a'), 'A')
        self.assertEqual(dla.getValue('b'), '\xc3\xab')
        self.assertEqual(dla.getValue('c'), u'xeb')
        self.assertEqual(dla.getValue('d'), 42)
        self.assertEqual(dla.getValue('e'), None)
        self.assertEqual(dla.getValue('e', 'default'), 'default')

        # Switch the keys and values around.
        b = (('A', 'a',), ('\xc3\xab', 'b'), (u'xeb', 'c'))
        dlb = DisplayList(b)
        self.assertEqual(dlb.getValue('A'), 'a')
        self.assertEqual(dlb.getValue('\xc3\xab'), 'b')
        self.assertEqual(dlb.getValue(u'xeb'), 'c')
        self.assertEqual(dlb.getValue('e'), None)
        self.assertEqual(dlb.getValue('e', 'default'), 'default')


class IntDisplayListTest(ATTestCase):

    def test_cmp(self):
        ta = (1, 2, 3)
        tb = (1, 3, 2)
        td = (3, 2, 1)
        self.assertTrue(IntDisplayList(zip(ta, ta)) ==
                        IntDisplayList(zip(ta, ta)))
        self.assertFalse(IntDisplayList(zip(ta, ta)) ==
                         IntDisplayList(zip(ta, tb)))
        self.assertTrue(IntDisplayList(zip(ta, ta)) ==
                        IntDisplayList(zip(td, td)))
        self.assertTrue(IntDisplayList(zip(tb, ta)) ==
                        IntDisplayList(zip(tb, ta)))
        self.assertRaises(TypeError, cmp, IntDisplayList(), '')

    def test_slice(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        sub = l[1:]
        self.assertTrue(IntDisplayList(l)[1:] == sub)

    def test_item(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        for i in range(0, 2):
            item = ta[i]
            self.assertTrue(IntDisplayList(l)[i] == item)

    def test_add(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)[:]
        self.assertTrue(dl == l)
        l.append((4, 4))
        dl.append((4, 4))
        self.assertTrue(dl == l)

    def test_len(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(len(dl) == len(l))

    def test_keys(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(tuple(dl.keys()) == ta)

    def test_values(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(tuple(dl.values()) == ta)

    def test_items(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(dl.items() == tuple(l))

    def test_repr(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(repr(dl).find(str(l)))

    def test_str(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(str(dl) == str(l))

    def test_call(self):
        ta = (1, 2, 3)
        l = zip(ta, ta)
        dl = IntDisplayList(l)
        self.assertTrue(dl == dl)
        self.assertTrue(dl() == dl())
        self.assertTrue(dl[:] == l)
        self.assertTrue(dl()[:] == l)

    def test_sort(self):
        a = ((1, 'a',), (2, 'b'), (3, 'c'))
        b = ((10, 'Z',), (9, 'Y'), (8, 'X'))
        c = ((1, 'Z',), (3, 'Y'), (2, 'X'))
        dla = IntDisplayList(a)
        dlb = IntDisplayList(b)
        dlc = IntDisplayList(c)

        assert dla.values() == ['a', 'b', 'c']
        dlb_s = dlb.sortedByValue()
        assert dlb_s.values() == ['X', 'Y', 'Z']
        dlc_s = dlc.sortedByKey()
        assert dlc_s.values() == ['Z', 'X', 'Y']

    def test_getValue(self):
        a = ((1, 'A',), (2, '\xc3\xab'), (3, u'xeb'), (4, 42))
        dla = IntDisplayList(a)
        self.assertEqual(dla.getValue(1), 'A')
        self.assertEqual(dla.getValue(2), '\xc3\xab')
        self.assertEqual(dla.getValue(3), u'xeb')
        self.assertEqual(dla.getValue(4), 42)
        self.assertEqual(dla.getValue(5), None)
        self.assertEqual(dla.getValue(5, 'default'), 'default')


class VocabularyTest(ATTestCase):

    def test_getValue(self):
        a = (('a', 'A',), ('b', '\xc3\xab'), ('c', u'xeb'), ('d', 42))
        dla = DisplayList(a)
        va = Vocabulary(dla, instance=None, i18n_domain=None)
        self.assertEqual(va.getValue('a'), 'A')
        self.assertEqual(va.getValue('b'), '\xc3\xab')
        self.assertEqual(va.getValue('c'), u'xeb')
        self.assertEqual(va.getValue('d'), 42)
        self.assertEqual(va.getValue('e'), None)
        self.assertEqual(va.getValue('e', 'default'), 'default')

        b = (('A', 'a',), ('\xc3\xab', 'b'), (u'xeb', 'c'))
        dlb = DisplayList(b)
        vb = Vocabulary(dlb, instance=None, i18n_domain=None)
        self.assertEqual(vb.getValue('A'), 'a')
        self.assertEqual(vb.getValue('\xc3\xab'), 'b')
        self.assertEqual(vb.getValue(u'xeb'), 'c')
        self.assertEqual(vb.getValue('e'), None)
        self.assertEqual(vb.getValue('e', 'default'), 'default')

        c = ((1, 'A',), (2, '\xc3\xab'), (3, u'xeb'), (4, 42))
        dlc = IntDisplayList(c)
        vb = Vocabulary(dlc, instance=None, i18n_domain=None)
        self.assertEqual(dlc.getValue(1), 'A')
        self.assertEqual(dlc.getValue(2), '\xc3\xab')
        self.assertEqual(dlc.getValue(3), u'xeb')
        self.assertEqual(dlc.getValue(4), 42)
        self.assertEqual(dlc.getValue(5), None)
        self.assertEqual(dlc.getValue(5, 'default'), 'default')

    def test_translating_getValue(self):
        # We use the same base displaylists as above (hopefully), but
        # now we pass an instance and an i18n_domain.  The instance is
        # expected to be an Archetypes object, but currently it only
        # needs to have a True boolean value.
        a = (('a', 'A',), ('b', '\xc3\xab'), ('c', u'xeb'), ('d', 42))
        dla = DisplayList(a)
        va = Vocabulary(dla, instance=object(), i18n_domain='plone')
        self.assertEqual(va.getValue('a'), 'A')
        self.assertEqual(va.getValue('b'), '\xc3\xab'.decode('utf-8'))
        self.assertEqual(va.getValue('c'), u'xeb')
        self.assertEqual(va.getValue('d'), 42)
        self.assertEqual(va.getValue('e'), None)
        self.assertEqual(va.getValue('e', 'default'), 'default')

        b = (('A', 'a',), ('\xc3\xab', 'b'), (u'xeb', 'c'))
        dlb = DisplayList(b)
        vb = Vocabulary(dlb, instance=object(), i18n_domain='plone')
        self.assertEqual(vb.getValue('A'), 'a')
        self.assertEqual(vb.getValue('\xc3\xab'), 'b')
        self.assertEqual(vb.getValue(u'xeb'), 'c')
        self.assertEqual(vb.getValue('e'), None)
        self.assertEqual(vb.getValue('e', 'default'), 'default')

        c = ((1, 'A',), (2, '\xc3\xab'), (3, u'xeb'), (4, 42))
        dlc = IntDisplayList(c)
        vb = Vocabulary(dlc, instance=object(), i18n_domain='plone')
        self.assertEqual(dlc.getValue(1), 'A')
        self.assertEqual(dlc.getValue(2), '\xc3\xab')
        self.assertEqual(dlc.getValue(3), u'xeb')
        self.assertEqual(dlc.getValue(4), 42)
        self.assertEqual(dlc.getValue(5), None)
        self.assertEqual(dlc.getValue(5, 'default'), 'default')
