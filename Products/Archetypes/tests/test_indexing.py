"""
Unittests for a Schema Provider

$Id: test_indexing.py,v 1.1.2.1 2004/04/21 16:29:04 bcsaller Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Acquisition import aq_base
import Products.Archetypes.config as config
from Products.Archetypes.public import *
from Products.Archetypes.examples.DDocument import schema as DDocumentSchema
from Products.Archetypes.Extensions.utils import install_indexes

class Dummy(BaseContent):
    schema = BaseSchema + Schema((
        StringField('fullauto',
                    index=("FieldIndex:brains",)
                    ),
        StringField('supplied',
                    accessor="getFoo",
                    index=("TextIndex",)
                    ),
        StringField('infered'), # but provided
        ))

    def getFoo(self):
        """this should add extra stuff"""
        return self.Schema()['supplied'].get(self) + "bar"

    def getInfered(self):
        """just return a static"""
        return "Infered Var"



class IndexingTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager(None, user)
        portal = self.getPortal()
        install_indexes(portal, None, (Dummy,))

        d  = Dummy(oid='dummy')
        portal._setObject('dummy', d)
        self._dummy = getattr(self.getPortal(), 'dummy')


    def test_simpleIndexing(self):
        # if this works portal_catalog should have indexes for
        # fullauto and supplied and fullauto should be in the brains
        portal = self.getPortal()
        catalog = portal.portal_catalog

        # Now lets assert a few things
        assert 'fullauto' in catalog.schema()
        assert 'supplied' not in catalog.schema()

        assert 'fullauto' in  catalog.indexes()
        assert 'supplied' in  catalog.indexes()

        # Now lets do some intergration testing
        d = self._dummy
        d.set('fullauto', "uniquestring")
        d.set('supplied', "This is a field with foo")
        d.reindexObject()

        #and we look for it
        res = catalog(fullauto="uniquestring")
        assert res[0].getObject() == d
        res = catalog(supplied="foobar") # The accessor would have
        # appended bar so "foo" is indexed as "foobar" if this is working
        assert res[0].getObject() == d


if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(IndexingTests))
        return suite
