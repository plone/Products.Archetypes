import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import * 
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



class TestReferenceEngine(ArchetypesTestCase):
    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self) 
        self.re = ReferenceEngine()

    def beforeTearDown(self): 
        del self.re
        ArchetypesTestCase.beforeTearDown(self)

    def test_clearBrefs(self):
        re = self.re
        ar = re.addReference
        gr = re.getRefs
        gb = re.getBRefs
        a = 'a'
        b = 'b'
        c = 'c'

        ar(a, b, 'KnowsAbout')
        ar(a, b, 'Includes')
        assert len(gr(a)) == 2
        ar(a, c, 'FooBar')
        assert len(gr(a)) == 3

        #delete the refs to C
        re.deleteReference(a, c)
        assert gb(c) == []
        assert gr(a, 'FooBar') == []

        assert gb(a) == [] #How could this ever happen, but still
        assert gr(c) == [] #Again, impossible

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


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestReferenceEngine))
        return suite
 