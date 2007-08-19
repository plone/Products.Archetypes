################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""
"""

__author__ = 'Christian Heimes'
__docformat__ = 'restructuredtext'

from Testing.ZopeTestCase import FunctionalDocFileSuite as FileSuite

# a list of dotted paths to modules which contains doc tests
DOCTEST_MODULES = (
    'Products.Archetypes.utils',
    'Products.Archetypes.Schema',
    'Products.Archetypes.ArchetypeTool',
    'Products.Archetypes.AllowedTypesByIface',
    'Products.Archetypes.Field',
    'Products.Archetypes.Marshall',
    'Products.Archetypes.fieldproperty',
    'Products.Archetypes.browser.widgets',
    )

PLONE_DOCTEST_FILES = ('events.txt',
                       'editing.txt')

HAS_PLONE = True
try:
    from Products.CMFPlone.tests.PloneTestCase import FunctionalTestCase
except ImportError:
    HAS_PLONE = False


from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.atsitetestcase import ATFunctionalSiteTestCase
from Products.Archetypes.tests.doctestcase import ZopeDocTestSuite

def test_suite():
    suite = ZopeDocTestSuite(test_class=ATSiteTestCase,
                             extraglobs={},
                             *DOCTEST_MODULES
                             )
    if HAS_PLONE:
        for testfile in PLONE_DOCTEST_FILES:
            suite.addTest(FileSuite(testfile,
                                    package="Products.Archetypes.tests",
                                    test_class=FunctionalTestCase)
                         )
    return suite
