"""
"""
__author__ = 'Christian Heimes'
__docformat__ = 'restructuredtext'

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

# a list of dotted paths to modules which contains doc tests
PORTALDOCTEST_MODULES = (
    )

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.doctestcase import ZopeDocTestSuite
from Products.CMFCore.utils import getToolByName

def test_suite():
    suite = ZopeDocTestSuite(test_class=ATSiteTestCase,
                             extraglobs={'getToolByName' : getToolByName},
                             *PORTALDOCTEST_MODULES
                             )
    return suite

if __name__ == '__main__':
    framework()
