"""
Unittests for a renaming archetypes objects.

$Id: test_rename.py,v 1.7 2003/07/10 21:19:14 dreamcatcher Exp $
"""

import unittest
import Zope

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Acquisition import aq_base
from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.Archetypes.tests.test_sitepolicy import makeContent
from Products.CMFPlone.Portal import manage_addSite

class RenameTests( SecurityRequestTest ):

    def setUp(self):
        SecurityRequestTest.setUp(self)
        manage_addSite( self.root, 'testsite', \
                        custom_policy='Archetypes Site' )

    def test_rename(self):
        site = self.root.testsite
        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(site, portal_type='Fact', id=obj_id)
        content = 'The book is on the table!'
        doc.setQuote(content)
        self.failUnless(str(doc.getQuote()) == str(content))
        #make sure we have _p_jar
        doc._p_jar = site._p_jar = self.root._p_jar
        new_oid = self.root._p_jar.new_oid
        site._p_oid = new_oid()
        doc._p_oid = new_oid()
        site.manage_renameObject(obj_id, new_id)
        doc = getattr(site, new_id)
        self.failUnless(str(doc.getQuote()) == str(content))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( RenameTests ) )
    return suite

if __name__ == '__main__':
    unittest.main( defaultTest = 'test_suite' )
