# -*- coding: iso-8859-1 -*-
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
from Testing import ZopeTestCase

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.lib.baseunit import BaseUnit

from types import StringType

class DummyDiscussionTool:
    def isDiscussionAllowedFor( self, content ):
        return False
    def overrideDiscussionFor(self, content, allowDiscussion):
        pass

MULTIPLEFIELD_LIST = DisplayList(
    (
    ('1', 'Option 1 : printemps'),
    ('2', 'Option 2 : été'),
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
        self._dummy = mkDummyInContext(Dummy, oid='dummy', context=self.getPortal(),
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
        self.assertEquals(searchable, '1 2 Option 1 : printemps Option 2 : été')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(BaseObjectTest))
    return suite

if __name__ == '__main__':
    framework()
