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
        self.firstname = ''
        self.lastname = ''

    def get_name(self, name, instance, **kwargs):
        """ aggregator """
        return {'whole_name' : instance.firstname + " " + instance.lastname }

    def set_name(self, name, instance, value, **kwargs):
        """ disaggregator """
        try:
            firstname, lastname = value.split(' ')
        except:
            firstname = lastname = ''
        setattr(instance, 'firstname', firstname)
        setattr(instance, 'lastname', lastname)
 
registerType(Dummy)

tests = []

class AggregatedStorageTest(unittest.TestCase):

    def setUp(self):
        self._storage = AggregatedStorage()
        self._storage.registerAggregator('whole_name', 'get_name')
        self._storage.registerDisaggregator('whole_name', 'set_name')

        
        schema = Schema( (StringField('whole_name', storage=self._storage),
                         )) 

        self._instance = Dummy('dummy')
        self._instance.schema = schema


    def test_basetest(self):
        field = self._instance.Schema()['whole_name']
        
        self.assertEqual(field.get(self._instance).strip(), '')
        field.set(self._instance, 'Donald Duck')
        self.assertEqual(self._instance.firstname, 'Donald')
        self.assertEqual(self._instance.lastname, 'Duck')
        self.assertEqual(field.get(self._instance).strip(), 'Donald Duck')
        
        self._instance.firstname = 'Daniel'
        self._instance.lastname = 'Düsentrieb'
        self.assertEqual(field.get(self._instance).strip(), 'Daniel Düsentrieb')

        field.set(self._instance, 'Bingo Gringo')
        self.assertEqual(self._instance.firstname, 'Bingo')
        self.assertEqual(self._instance.lastname, 'Gringo')




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
