"""
Unittests for a renaming archetypes objects.

$Id: test_rename.py,v 1.12.16.1 2004/05/13 15:59:17 shh42 Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_rename', 'Cannot import ArcheSiteTestCase')


class RenameTests(ArcheSiteTestCase):

    def test_rename(self):
        obj_id = 'demodoc'
        new_id = 'new_demodoc'
        doc = makeContent(self.folder, portal_type='Fact', id=obj_id)
        content = 'The book is on the table!'
        doc.setQuote(content, mimetype="text/plain")
        self.failUnless(str(doc.getQuote()) == str(content))
        #make sure we have _p_jar
        get_transaction().commit(1)
        self.folder.manage_renameObject(obj_id, new_id)
        doc = getattr(self.folder, new_id)
        self.failUnless(str(doc.getQuote()) == str(content))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(RenameTests))
    return suite

if __name__ == '__main__':
    framework()
