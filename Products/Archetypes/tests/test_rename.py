"""
Unittests for a renaming archetypes objects.

$Id: test_rename.py,v 1.8.4.3 2003/10/21 15:22:36 tiran Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import * 

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')

from Acquisition import aq_base
from Products.Archetypes.tests.test_sitepolicy import makeContent

class RenameTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self) 
        user = self.getManagerUser()
        newSecurityManager( None, user )

    # XXX test is not running: ValueError: can not change oid of cached object
    def test_rename(self):
        site = self.getPortal()
        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(site, portal_type='Fact', id=obj_id)
        content = 'The book is on the table!'
        doc.setQuote(content, mimetype="text/plain")
        self.failUnless(str(doc.getQuote()) == str(content))
        #make sure we have _p_jar
        doc._p_jar = site._p_jar = self.app._p_jar
        new_oid = self.app._p_jar.new_oid
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
