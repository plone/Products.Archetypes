import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

import unittest

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


class AggregatedStorageTestsNoCache(unittest.TestCase):

    caching = 0

    def setUp(self):
        self._storage = AggregatedStorage(caching=self.caching)
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
        self._instance.lastname = 'Dosentrieb'
        self.assertEqual(field.get(self._instance).strip(), 'Daniel Dosentrieb')

        field.set(self._instance, 'Bingo Gringo')
        self.assertEqual(self._instance.firstname, 'Bingo')
        self.assertEqual(self._instance.lastname, 'Gringo')


class AggregatedStorageTestsWithCache(AggregatedStorageTestsNoCache):

    caching = 1


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(AggregatedStorageTestsNoCache))
    suite.addTest(makeSuite(AggregatedStorageTestsWithCache))
    return suite

if __name__ == '__main__':
    framework()
