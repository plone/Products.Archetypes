import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Products.Archetypes.lib.vocabulary import OrderedDict


class OrderedDictTest( ArchetypesTestCase ):

    def afterSetUp(self):
        self.d = OrderedDict()
        self.d['a'] = '1'
        self.d['b'] = '2'
        self.d['c'] = '3'

    def test_order(self):
        self.failUnless(self.d.keys() == ['a','b','c'])
        self.failUnless(self.d.values() == ['1','2','3'])
        self.failUnless(self.d.items() == [('a','1'),('b','2'),('c','3')])
        self.failUnless(self.d.reverse() == [('c','3'),('b','2'),('a','1')])

    def test_setitem(self):
        self.d['d'] = '4'
        self.failUnless(self.d.keys() == ['a','b','c','d'])
        self.failUnless(self.d.values() == ['1','2','3','4'])
        self.failUnless(self.d.items() == [('a','1'),('b','2'),('c','3'),('d','4')])
        self.failUnless(self.d.reverse() == [('d','4'),('c','3'),('b','2'),('a','1')])

        self.d['c'] = 'C'
        self.failUnless(self.d.keys() == ['a','b','c','d'])
        self.failUnless(self.d.values() == ['1','2','C','4'])
        self.failUnless(self.d.items() == [('a','1'),('b','2'),('c','C'),('d','4')])
        self.failUnless(self.d.reverse() == [('d','4'),('c','C'),('b','2'),('a','1')])

    def test_del(self):
        del self.d['b']
        self.failUnless(self.d.keys() == ['a','c'])
        self.failUnless(self.d.values() == ['1','3'])
        self.failUnless(self.d.items() == [('a','1'),('c','3')])
        self.failUnless(self.d.reverse() == [('c','3'),('a','1')])
        self.failIf(self.d.has_key('b'))
        self.failUnless(self.d.get('b',None) == None)

    def test_clear(self):
        self.d.clear()
        self.failUnless(self.d.keys() == [])
        self.failUnless(self.d.values() == [])
        self.failUnless(self.d.items() == [])
        self.failUnless(self.d.reverse() == [])

    def test_update(self):
        d2 = {'b':'B','d':'4'}
        self.d.update(d2)
        self.failUnless(self.d.keys() == ['a','b','c','d'])
        self.failUnless(self.d.values() == ['1','B','3','4'])
        self.failUnless(self.d.items() == [('a','1'),('b','B'),('c','3'),('d','4')])
        self.failUnless(self.d.reverse() == [('d','4'),('c','3'),('b','B'),('a','1')])

    def test_popitem(self):
        (k,v) = self.d.popitem()
        self.failUnless(k == 'c')
        self.failUnless(v == '3')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(OrderedDictTest))
    return suite

if __name__ == '__main__':
    framework()
