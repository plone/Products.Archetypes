import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *
from Products.Archetypes.AggregatedStorage import AggregatedStorage
from Products.Archetypes.public import Schema, StringField, BaseContent
from Products.Archetypes.public import registerType


class Dummy(BaseContent):

    def __init__(self, oid, **kwargs):
        BaseContent.__init__(self, oid, **kwargs)
        self.initializeArchetype()
 
registerType(Dummy)

tests = []

class AggregatedStorageTest(unittest.TestCase):

    def setUp(self):
        self._storage = AggregatedStorage()
        self._storage.registerAggregator('firstname', 'ag_firstname')
        self._storage.registerAggregator('lastname', 'ag_lastname')
        self._storage.registerDisaggregator('firstname', 'dag_firstname')
        self._storage.registerDisaggregator('lastname', 'dag_lastname')

        
        schema = Schema( (StringField('firstname', storage=self._storage),
                          StringField('lastname', storage=self._storage),
                         )) 

        self._instance = Dummy('dummy')
        self._instance.schema = schema

    def test_basetest(self):
#        self.assertRaises(KeyError, self._storage.registerDisaggregator, ('lastname', 'dag_lastname'))
        pass


tests.append(AggregatedStorageTest)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        for test in tests:
            suite.addTest(unittest.makeSuite(test))
        return suite
