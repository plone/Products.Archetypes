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

from Acquisition import aq_base
from Acquisition import aq_parent

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.tests.utils import gen_class
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import schema

from types import FunctionType, ListType, TupleType

from Products.Archetypes.atapi import *
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.config import PKG_NAME
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

fieldList = [
    # (accessor, mutator, field),
    ('Title', 'setTitle',                    ''),
    ('Creator', '',                          ''),
    ('Subject','setSubject',                 'subject'),
    ('Description','setDescription',         'description'),
    ('Publisher', '',                        ''),
    ('Contributors','setContributors',       'contributors'),
    ('Date', '',                             ''),
    ('CreationDate', '',                     ''),
    ('EffectiveDate','setEffectiveDate',     'effectiveDate'),
    ('ExpirationDate','setExpirationDate',   'expirationDate'),
    ('ModificationDate', '',                 ''),
    ('Type', '',                             ''),
    ('Format', 'setFormat',                  ''),
    ('Identifier', '',                       ''),
    ('Language','setLanguage',               'language'),
    ('Rights','setRights',                   'rights'),

    # allowDiscussion is not part of the official DC metadata set
    ('allowDiscussion','isDiscussable','allowDiscussion'),
  ]

class DummyPortalMembership:
    def checkPermission(self, *args, **kwargs):
        return True

def addMetadataTo(obj, data='default', mimetype='application/octet-stream', time=1000):
    """ """
    obj.setTitle(data)
    obj.setSubject([data])
    obj.setDescription(data)
    obj.setContributors([data])
    obj.setEffectiveDate(DateTime(time, 0))
    obj.setExpirationDate(DateTime(time, 0))
    obj.setFormat(mimetype)
    obj.setLanguage(data)
    obj.setRights(data)

def compareMetadataOf(test, obj, data='default', mimetype='application/octet-stream', time=1000):
    l_data = (data,)
    test.failUnless(obj.Title() == data, 'Title')
    test.failUnless(obj.Subject() == l_data,
                    'Subject: %s, %s' % (obj.Subject(), l_data))
    test.failUnless(obj.Description() == data, 'Description')
    test.failUnless(obj.Contributors() == l_data, 'Contributors')
    test.failUnless(obj.EffectiveDate() == DateTime(time, 0).ISO(),
                    'effective date')
    test.failUnless(obj.ExpirationDate() == DateTime(time, 0).ISO(),
                    'expiration date')
    # XXX BROKEN! test.failUnless(obj.Format() == data,
    #                             'Format: %s, %s' % (obj.Format(), mimetype))
    test.failUnless(obj.Language() == data, 'Language')
    test.failUnless(obj.Rights() == data, 'Rights')


class DummyFolder(BaseFolder):

    portal_membership = DummyPortalMembership()


class ExtensibleMetadataTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(klass=Dummy, oid='dummy',
                                       context=self.getPortal(), schema=schema)
        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])
        self.makeDummy()
        addMetadataTo(self._dummy)

    def makeDummy(self):
        return self._dummy

    def testAccessors(self):
        obj = self._dummy
        for field in fieldList:
            accessor = field[0]
            fobj = getattr(obj, accessor, None)
            if not fobj:
                self.fail('Missing accessor for field: %s' % str(field))
            self.failUnless(hasattr(obj, accessor),
                            'Missing accessor %s' % accessor)
            self.failUnless((type(fobj) is FunctionType or
                             hasattr(fobj, '__call__')),
                            'Accessor %s is not callable' % accessor)

    def testMutators(self):
        obj = self._dummy
        for field in fieldList:
            mutator = field[1]
            if not mutator: continue
            fobj = getattr(obj, mutator, None)
            self.failUnless(hasattr(obj, mutator),
                            'Missing mutator %s' % mutator)
            self.failUnless((type(fobj) is FunctionType
                             or hasattr(fobj, '__call__')),
                            'Mutator %s is not callable' % mutator)

    def testMetaFields(self):
        obj = self._dummy
        for field in fieldList:
            meta = field[2]
            if not meta: continue
            md = aq_base(obj)._md
            field = aq_base(obj).Schema()[meta]
            self.failUnless(md.has_key(meta), 'Missing field %s' % meta)
            _marker = []
            value = md.get(meta, _marker)
            # We are checking here if the metadata
            # for a given field has been correctly initialized.
            self.failIf(value is _marker,
                        'Metadata field %s has not been correctly '
                        'initialized.' % meta)
            self.failUnless(field.isMetadata,
                            'isMetadata not set correctly for field %s.' % meta)


class ExtMetadataContextTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self._dummy = mkDummyInContext(klass=Dummy, oid='dummy',
                                       context=self.getPortal(), schema=schema)
        gen_class(DummyFolder)
        portal = self.getPortal()

        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])

        parent = mkDummyInContext(klass=DummyFolder, oid='parent',
                                  context=portal, schema=None)
        self._parent = parent

        # create dummy in context of a plone folder
        self._dummy = mkDummyInContext(klass=Dummy, oid='dummy',
                                       context=parent, schema=None)

    def testContext(self):
        addMetadataTo(self._parent, data='parent', time=1001)
        addMetadataTo(self._parent.dummy, data='dummy', time=9998)

        compareMetadataOf(self, self._parent, data='parent', time=1001)
        compareMetadataOf(self, self._parent.dummy, data='dummy', time=9998)

    def testUnwrappedContext(self):
        addMetadataTo(self._parent, data='parent', time=1001)
        addMetadataTo(self._parent.dummy, data='dummy', time=9998)

        compareMetadataOf(self, aq_base(self._parent), data='parent', time=1001)
        compareMetadataOf(self, aq_base(self._parent.dummy), data='dummy', time=9998)

    def testIsParent(self):
        portal = self.getPortal()
        self.failUnless(aq_parent(self._parent) == portal)
        dummy_parent = aq_base(aq_parent(self._parent.dummy))
        parent = aq_base(self._parent)
        self.failUnless(dummy_parent is parent,
                        ('Parent is not the parent of dummy! '
                         'Some tests will give you false results!'))


class ExtMetadataDefaultLanguageTest(ATSiteTestCase):

    def testDefaultLanguage(self):
        # This is handled at creation time, so the prop must be set
        # then, its not a runtime fallback to the property
        language = 'no'

        portal = self.getPortal()
        try:
            sp = getToolByName(portal, 'portal_properties').site_properties
        except AttributeError:
            # XXX CMF doesn't have site properties
            pass
        else:
            sp._updateProperty('default_language', language)

        #Create a proper object
        self.folder.invokeFactory(id="dummy",
                                  type_name="SimpleType")
        dummy = getattr(self.folder, 'dummy')
        self.failUnlessEqual(dummy.Language(), language)

class ExtMetadataSetFormatTest(ATSiteTestCase):

    value = "fooooo"
    filename = 'foo.txt'

    def afterSetUp(self):
        portal = self.getPortal()

        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])

        parent = mkDummyInContext(DummyFolder, oid='parent', context=portal, schema=None)
        self._parent = parent

        # create dummy in context of a plone folder
        dummy = mkDummyInContext(Dummy, oid='dummy', context=parent, schema=None)
        self._dummy = dummy

        pfield = dummy.getPrimaryField()
        # tests do need afilefield
        self.failUnlessEqual(pfield.getName(), 'afilefield')
        pfield.set(dummy, self.value, filename=self.filename, mimetype='text/plain')

        self._parent.dummy = dummy

    def testSetFormat(self):
        dummy = self._parent.dummy
        pfield = dummy.getPrimaryField()

        self.failUnlessEqual(dummy.Format(), 'text/plain')
        self.failUnlessEqual(dummy.getContentType(), 'text/plain')
        self.failUnlessEqual(dummy.content_type, 'text/plain')
        self.failUnlessEqual(dummy.get_content_type(), 'text/plain')
        self.failUnlessEqual(pfield.getContentType(dummy), 'text/plain')
        self.failUnlessEqual(pfield.get(dummy).content_type, 'text/plain')

        dummy.setFormat('image/gif')
        self.failUnlessEqual(dummy.Format(), 'image/gif')
        self.failUnlessEqual(dummy.getContentType(), 'image/gif')
        self.failUnlessEqual(dummy.content_type, 'image/gif')
        self.failUnlessEqual(dummy.get_content_type(), 'image/gif')
        self.failUnlessEqual(pfield.getContentType(dummy), 'image/gif')
        self.failUnlessEqual(pfield.get(dummy).content_type, 'image/gif')

    def testSetContentType(self):
        dummy = self._parent.dummy
        pfield = dummy.getPrimaryField()

        dummy.setContentType('text/plain')
        self.failUnlessEqual(dummy.Format(), 'text/plain')
        self.failUnlessEqual(dummy.getContentType(), 'text/plain')
        self.failUnlessEqual(dummy.content_type, 'text/plain')
        self.failUnlessEqual(dummy.get_content_type(), 'text/plain')
        self.failUnlessEqual(pfield.getContentType(dummy), 'text/plain')
        self.failUnlessEqual(pfield.get(dummy).content_type, 'text/plain')

        dummy.setContentType('image/gif')
        self.failUnlessEqual(dummy.Format(), 'image/gif')
        self.failUnlessEqual(dummy.getContentType(), 'image/gif')
        self.failUnlessEqual(dummy.content_type, 'image/gif')
        self.failUnlessEqual(dummy.get_content_type(), 'image/gif')
        self.failUnlessEqual(pfield.getContentType(dummy), 'image/gif')
        self.failUnlessEqual(pfield.get(dummy).content_type, 'image/gif')


    def testMultipleChanges(self):
        dummy = self._parent.dummy
        pfield = dummy.getPrimaryField()

        dummy.setContentType('image/gif')
        self.failUnlessEqual(dummy.getContentType(), 'image/gif')
        dummy.setFormat('application/pdf')
        self.failUnlessEqual(dummy.Format(), 'application/pdf')
        dummy.setContentType('image/jpeg')
        self.failUnlessEqual(dummy.Format(), 'image/jpeg')

        self.failUnlessEqual(pfield.get(dummy).filename, self.filename)
        self.failUnlessEqual(pfield.get(dummy).data, self.value)

    def testChangesOnFieldChangesObject(self):
        dummy = self._parent.dummy
        pfield = dummy.getPrimaryField()

        data = pfield.get(dummy)
        self.failUnlessEqual(data.content_type, 'text/plain')

        data.content_type = 'image/jpeg'

        self.failUnlessEqual(data.content_type, 'image/jpeg')

        pfield.set(dummy, data)
        self.failUnlessEqual(dummy.Format(), 'image/jpeg')
        self.failUnlessEqual(dummy.getContentType(), 'image/jpeg')
        self.failUnlessEqual(dummy.content_type, 'image/jpeg')
        self.failUnlessEqual(dummy.get_content_type(), 'image/jpeg')
        self.failUnlessEqual(pfield.getContentType(dummy), 'image/jpeg')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ExtensibleMetadataTest))
    suite.addTest(makeSuite(ExtMetadataContextTest))
    suite.addTest(makeSuite(ExtMetadataDefaultLanguageTest))
    suite.addTest(makeSuite(ExtMetadataSetFormatTest))
    return suite

if __name__ == '__main__':
    framework()
