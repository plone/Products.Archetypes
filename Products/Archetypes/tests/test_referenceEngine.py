import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.ReferenceEngine import ReferenceEngine
from Products.CMFCore  import CMFCorePermissions

from DateTime import DateTime
import unittest

class ReferenceEngine(ReferenceEngine):
    def assertId(self, uid):
        return 1
    


class TestReferenceEngine(unittest.TestCase):
    def setUp(self):
        self.re = ReferenceEngine()

    def tearDown( self ):
        del self.re

    def test_delete(self):
        re = self.re
        ar = re.addReference
        gr = re.getRefs
        gb = re.getBRefs
        a = 'a'
        b = 'b'
        c = 'c'

        ar(a, b, 'KnowsAbout')
        ar(a, b, 'Includes')
        ar(a, c, 'KnowsAbout')

        assert len(gr(a, 'KnowsAbout')) == 2
        assert len(gr(a, 'Includes')) == 1

        #delete includes
        re.deleteReferences(a, 'Includes')
        assert len(gr(a, 'Includes')) == 0
        assert len(gr(a, 'KnowsAbout')) == 2
        assert len(gb(b)) == 1
        assert len(gb(c)) == 1

        re.deleteReferences(a)
        assert gr(a) == []
        assert gb(b) == []
        assert gb(c) == []
        

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestReferenceEngine),
        ))

if __name__ == '__main__':
    unittest.main()
