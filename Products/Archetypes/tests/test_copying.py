"""
Unittests for a copying/cutting and pasting archetypes objects.

$Id: test_copying.py,v 1.1.2.1 2004/06/09 03:46:39 andrecamargo Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_copying', 'Cannot import ArcheSiteTestCase')


class CutPasteCopyPasteTests(ArcheSiteTestCase):

    def test_copy_and_paste(self):
        ffrom = makeContent(self.folder, portal_type='SimpleFolder', id='cangucu')
        tourist = makeContent(ffrom, portal_type='Fact', id='tourist')
        fto = makeContent(self.folder, portal_type='SimpleFolder', id='london')
        #make sure we have _p_jar
        #get_transaction().commit(1)
        self.failIf('tourist' not in ffrom.contentIds())

        fto.manage_pasteObjects(ffrom.manage_copyObjects(ffrom.contentIds()))
        #get_transaction().commit(1)
        #fto.manage_pasteObjects()
        get_transaction().commit(1)
        self.failIf('tourist' not in ffrom.contentIds())
        self.failIf('tourist' not in fto.contentIds())

    def test_cut_and_paste(self):
        ffrom = makeContent(self.folder, portal_type='SimpleFolder', id='cangucu')
        tourist = makeContent(ffrom, portal_type='Fact', id='tourist')
        fto = makeContent(self.folder, portal_type='SimpleFolder', id='london')
        #make sure we have _p_jar
        #get_transaction().commit(1)
        self.failIf('tourist' not in ffrom.contentIds())

        fto.manage_pasteObjects(ffrom.manage_cutObjects(ffrom.contentIds()))
        #get_transaction().commit(1)
        #fto.manage_pasteObjects()
        get_transaction().commit(1)
        self.failIf('tourist' in ffrom.contentIds())
        self.failIf('tourist' not in fto.contentIds())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(CutPasteCopyPasteTests))
    return suite

if __name__ == '__main__':
    framework()
