"""
Unittests for a renaming archetypes objects.

$Id: test_rename.py,v 1.8.4.1 2003/10/20 17:09:17 tiran Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import * 

from Acquisition import aq_base
from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.CMFPlone.Portal import manage_addSite

# XXX
class RenameTests( ArchetypesTestCase, SecurityRequestTest ):

    def afterSetUp(self):
        ArchetypesTestCase.afterSetUp(self) 
        SecurityRequestTest.setUp(self)
        manage_addSite( self.root, 'testsite', \
                        custom_policy='Archetypes Site' )
    
    # XXX hangs up my process
    def __test_rename(self):
        site = self.root.testsite
        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(site, portal_type='Fact', id=obj_id)
        content = 'The book is on the table!'
        doc.setQuote(content, mimetype="text/plain")
        self.failUnless(str(doc.getQuote()) == str(content))
        #make sure we have _p_jar
        doc._p_jar = site._p_jar = self.root._p_jar
        new_oid = self.root._p_jar.new_oid
        site._p_oid = new_oid()
        doc._p_oid = new_oid()
        site.manage_renameObject(obj_id, new_id)
        doc = getattr(site, new_id)
        self.failUnless(str(doc.getQuote()) == str(content))

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(RenameTests))
        return suite 
