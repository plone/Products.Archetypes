"""
Unittests for a Schema Provider

$Id: test_classgen.py,v 1.18.10.2 2004/04/21 16:29:03 bcsaller Exp $
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
from Products.Archetypes.Schema.Provider import *
import Products.CMFCore.utils as utils
from Products.CMFCore import CMFCorePermissions


class Dummy(BaseContent):
    schema = BaseSchema + Schema((
        StringField('fullauto'),
        StringField('supplied', accessor="getFoo"),
        StringField('infered'), # but provided
        ))

    def getFoo(self):
        """this should add extra stuff"""
        return self.Schema()['supplied'].get(self) + "bar"

    def getInfered(self):
        """just return a static"""
        return "Infered Var"



class ClassGenTest( ArcheSiteTestCase ):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        registerType(Dummy)
        process_types(listTypes(), config.PKG_NAME)
        d  = Dummy(oid='dummy')
        self.getPortal()._setObject('dummy', d)
        self._dummy = getattr(self.getPortal(), 'dummy')
        user = self.getManagerUser()
        newSecurityManager(None, user)


    def test_methods(self):
        obj = self._dummy
        s = obj.Schema()
        f = s['fullauto']
        assert f.accessor == None

        f = s['infered']

        assert f.accessor == "getInfered"
        assert obj.get('infered') == "Infered Var"

        f = s['supplied']
        assert f.accessor == "getFoo"
        obj.set('supplied', 'foo')
        assert obj.get('supplied') == "foobar"

        f = s['title']
        assert f.accessor == "Title"
        assert f.mutator == "setTitle"
        # It really is the FS method
        assert f.getAccessor(obj).im_func.__name__ == "Title"

    def beforeTearDown(self):
        del self._dummy
        ArcheSiteTestCase.beforeTearDown(self)

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(ClassGenTest))
        return suite
