# -*- coding: UTF-8 -*-
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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME

from types import StringType

class DummyDiscussionTool:
    def isDiscussionAllowedFor( self, content ):
        return False
    def overrideDiscussionFor(self, content, allowDiscussion):
        pass

MULTIPLEFIELD_LIST = DisplayList(
    (
    ('1', 'Option 1 : printemps'),
    ('2', 'Option 2 : \xc3\xa9t\xc3\xa9'), # e-acute t e-acute
    ('3', 'Option 3 : automne'),
    ('4', 'Option 3 : hiver'),
    ))


schema = BaseSchema + Schema((
    LinesField(
        'MULTIPLEFIELD',
        searchable = 1,
        vocabulary = MULTIPLEFIELD_LIST,
        widget = MultiSelectionWidget(
            i18n_domain = 'plone',
            ),
        ), 
            ))


class Dummy(BaseContent):
   
    portal_discussion = DummyDiscussionTool()

    def getCharset(self):
         return 'iso-8859-1'
         
class BaseObjectTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(Dummy, oid='dummy', context=self.portal,
                                      schema=schema)
    
    def test_searchableText(self):
        """
        Fix bug [ 951955 ] BaseObject/SearchableText and list of Unicode stuffs
        """
        dummy = self._dummy
        
        
        # Set a multiple field
        dummy.setMULTIPLEFIELD(['1','2'])
        
        # Get searchableText
        searchable = dummy.SearchableText()
        
        # Test searchable type
        self.assertEquals(type(searchable), StringType)
        
        # Test searchable value
        self.assertEquals(searchable, '1 2 Option 1 : printemps Option 2 : \xc3\xa9t\xc3\xa9')

    def test_searchableTextUsesIndexMethod(self):
        """See https://dev.plone.org/archetypes/ticket/645

        We want SearchableText to use the ``index_method`` attribute
        of fields to determine which is the accessor it should use
        while gathering values.
        """
        ATSiteTestCase.afterSetUp(self)
        dummy = mkDummyInContext(Dummy, oid='dummy', context=self.portal,
                                 schema=schema.copy())
        
        # This is where we left off in the previous test
        dummy.setMULTIPLEFIELD(['1','2'])
        searchable = dummy.SearchableText()
        self.failUnless(searchable.startswith('1 2 Option 1 : printemps'))

        # Now we set another index_method and expect it to be used:
        dummy.getField('MULTIPLEFIELD').index_method = 'myMethod'
        def myMethod(self):
            return "What do you expect of a Dummy?"
        Dummy.myMethod = myMethod
        searchable = dummy.SearchableText()
        self.failUnless(searchable.startswith("What do you expect of a Dummy"))
        del Dummy.myMethod
        

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(BaseObjectTest))
    return suite

if __name__ == '__main__':
    framework()
