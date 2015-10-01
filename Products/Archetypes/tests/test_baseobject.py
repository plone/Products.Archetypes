##########################################################################
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
##########################################################################

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes import atapi


class DummyDiscussionTool:

    def isDiscussionAllowedFor(self, content):
        return False

    def overrideDiscussionFor(self, content, allowDiscussion):
        pass

MULTIPLEFIELD_LIST = atapi.DisplayList(
    (
        ('1', _(u'Option 1 : printemps')),
        ('2', unicode('Option 2 : \xc3\xa9t\xc3\xa9', 'utf-8')),  # e-acute t e-acute
        ('3', u'Option 3 : automne'),
        ('4', _(u'option3', default=u'Option 3 : hiver')),
    ))

schema = atapi.BaseSchema + atapi.Schema((
    atapi.LinesField(
        'MULTIPLEFIELD',
        searchable=1,
        vocabulary=MULTIPLEFIELD_LIST,
        widget=atapi.MultiSelectionWidget(
            i18n_domain='plone',
        ),
    ),
    atapi.TextField(
        'TEXTFIELD',
        primary=True,
    ),
))


class Dummy(atapi.BaseContent):

    portal_discussion = DummyDiscussionTool()

    def getCharset(self):
        return 'utf-8'


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
        dummy.setMULTIPLEFIELD(['1', '2'])
        searchable = dummy.SearchableText()

        self.assertTrue(isinstance(searchable, basestring))
        # Note: the vocabulary values used to get translated in some
        # cases, which during test runs would mean they would get
        # formatted as '[[plone][some value]]' instead of 'some value'.
        self.assertEqual(searchable,
                         '1 2 Option 1 : printemps Option 2 : \xc3\xa9t\xc3\xa9')

        dummy.setMULTIPLEFIELD(['3', '4'])
        searchable = dummy.SearchableText()

        self.assertEqual(searchable,
                         '3 4 Option 3 : automne option3')

    def test_searchableTextUsesIndexMethod(self):
        """See http://dev.plone.org/archetypes/ticket/645

        We want SearchableText to use the ``index_method`` attribute
        of fields to determine which is the accessor it should use
        while gathering values.
        """
        dummy = self._dummy

        # This is where we left off in the previous test
        dummy.setMULTIPLEFIELD(['1', '2'])
        searchable = dummy.SearchableText()
        self.assertTrue(searchable.startswith('1 2 Option 1 : printemps'))

        # Now we set another index_method and expect it to be used:
        dummy.getField('MULTIPLEFIELD').index_method = 'myMethod'

        def myMethod(self):
            return "What do you expect of a Dummy?"

        Dummy.myMethod = myMethod
        searchable = dummy.SearchableText()
        self.assertTrue(searchable.startswith("What do you expect of a Dummy"))
        del Dummy.myMethod

    def test_authenticatedContentType(self):
        """See https://dev.plone.org/archetypes/ticket/712

        content_type should not be protected by a security declaration, as
        it is usually an attribute. If a security declaration *is* set (in
        BaseObject or one of it's base classes) non-anonymous access from
        protected code (guarded_getattr) will fail.

        """
        from AccessControl.unauthorized import Unauthorized
        from AccessControl.Permissions import view
        from AccessControl.ZopeGuards import guarded_getattr

        dummy = self._dummy
        dummy.manage_permission(view, ('Manager',), False)
        # dummy.content_type in a Python Script
        self.assertRaises(Unauthorized, guarded_getattr, dummy, 'content_type')

        self.setRoles(('Manager',))
        # dummy.content_type in a Python Script
        self.assertEqual(guarded_getattr(dummy, 'content_type'), 'text/html')
