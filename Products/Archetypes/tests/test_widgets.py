import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

if not hasArcheSiteTestCase:
    raise TestPreconditionFailed('test_widgets', 'Cannot import ArcheSiteTestCase')

from Products.Archetypes.public import *
from OFS.Image import File
from DateTime import DateTime
from Acquisition import aq_base


from Products.Archetypes.tests.test_sitepolicy import makeContent

class WidgetTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager( None, user )

    def test_widgets(self):
        site = self.getPortal()
        doc = makeContent(site, portal_type='ComplexType', id='demodoc')

        #Now render this doc in view and edit modes. If this works
        #then we have pretty decent assurance that things are working
        view = doc.base_view()
        edit = doc.base_edit()

        #No exceptions are good, parse the results more if you need to
        #I feel fine...
        
        

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(WidgetTests))
        return suite
