import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.utils import DisplayList

import unittest

class DisplayListTest( unittest.TestCase ):

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
        self.failUnless(dl.getMsgId('a') == 'a')
        self.failUnless(dl.getMsgId('b') == 'bb')

    def test_concat(self):
        a = (('a','a',), ('b','b','bb'), ('c', 'c'))
        b = (('a','a','aa'), ('b','b'), ('c', 'c'))
        bzz, jzz = DisplayList(a), DisplayList(b)
        wahaaa = bzz + jzz
        self.failUnless(wahaaa.getMsgId('b') == 'bb')
        self.failUnless(wahaaa.getMsgId('a') == 'aa')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DisplayListTest),
        ))

if __name__ == '__main__':
    unittest.main()
