import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.utils import DisplayList


class DisplayListTest(ArchetypesTestCase):

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

    def test_getmsgid(self):
        ta = (('a','a',), ('b','b','bb'), ('c', 'c'))
        dl = DisplayList(ta)
        self.assertEquals(dl.getMsgId('a'), 'a')
        self.assertEquals(dl.getMsgId('b'), 'bb')

    def test_concat(self):
        a = (('a','a',), ('b','b','bb'), ('c', 'c'))
        b = (('a','a','aa'), ('b','b'), ('c', 'c'))
        bzz, jzz = DisplayList(a), DisplayList(b)
        wahaaa = bzz + jzz
        self.failUnless(wahaaa.getMsgId('b') == 'bb')
        self.failUnless(wahaaa.getMsgId('a') == 'aa')

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
    return suite

if __name__ == '__main__':
    framework()
