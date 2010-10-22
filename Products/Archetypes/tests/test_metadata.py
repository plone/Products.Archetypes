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

from Acquisition import aq_base
from Acquisition import aq_parent

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import mkDummyInContext
from Products.Archetypes.tests.utils import gen_class
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import schema

from types import FunctionType, ListType, TupleType

from Products.Archetypes.atapi import *
from Products.Archetypes import config
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.config import PKG_NAME
from ComputedAttribute import ComputedAttribute
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

def addMetadataTo(obj, data='default', mimetype='application/octet-stream', time=1980):
    """ """
    obj.setTitle(data)
    obj.setSubject([data])
    obj.setDescription(data)
    obj.setContributors([data])
    obj.setEffectiveDate(DateTime(time, 1))
    obj.setExpirationDate(DateTime(time, 1))
    obj.setFormat(mimetype)
    obj.setLanguage(data)
    obj.setRights(data)

def compareMetadataOf(test, obj, data='default',
                      mimetype='application/octet-stream', time=1980):
    l_data = (data,)
    test.failUnless(obj.Title() == data, 'Title')
    test.failUnless(obj.Subject() == l_data,
                    'Subject: %s, %s' % (obj.Subject(), l_data))
    test.failUnless(obj.Description() == data, 'Description')
    test.failUnless(obj.Contributors() == l_data, 'Contributors')
    test.failUnless(obj.EffectiveDate() == DateTime(time, 1).ISO8601(),
                    'effective date')
    test.failUnless(obj.ExpirationDate() == DateTime(time, 1).ISO8601(),
                    'expiration date')
    if aq_base(obj) is obj:
        # If the object is not acquisition wrapped, then those
        # ComputedAttributes won't get executed because the
        # declaration requires it to be wrapped
        # like: ComputedAttribute(method, 1)
        test.failUnless(isinstance(obj.effective_date, ComputedAttribute))
        test.failUnless(isinstance(obj.expiration_date, ComputedAttribute))
    else:
        test.failUnlessEqual(str(obj.effective_date),  str(DateTime(time, 1)))
        test.failUnlessEqual(str(obj.expiration_date), str(DateTime(time, 1)))
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
                                       context=self.portal, schema=schema)
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
                                       context=self.portal, schema=schema)
        gen_class(DummyFolder)
        portal = self.portal

        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])

        parent = mkDummyInContext(klass=DummyFolder, oid='parent',
                                  context=portal, schema=None)
        self._parent = parent

        # create dummy
        self._dummy = mkDummyInContext(klass=Dummy, oid='dummy',
                                       context=parent, schema=None)

    def testContext(self):
        addMetadataTo(self._parent, data='parent', time=1980)
        addMetadataTo(self._parent.dummy, data='dummy', time=2120)

        compareMetadataOf(self, self._parent, data='parent', time=1980)
        compareMetadataOf(self, self._parent.dummy, data='dummy', time=2120)

    def testUnwrappedContext(self):
        addMetadataTo(self._parent, data='parent', time=1980)
        addMetadataTo(self._parent.dummy, data='dummy', time=2120)

        compareMetadataOf(self, aq_base(self._parent), data='parent', time=1980)
        compareMetadataOf(self, aq_base(self._parent.dummy), data='dummy', time=2120)

    def testIsParent(self):
        portal = self.portal
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
        self.folder.invokeFactory(id="dummy",
                                  type_name="SimpleType")
        dummy = getattr(self.folder, 'dummy')
        self.failUnlessEqual(dummy.Language(), config.LANGUAGE_DEFAULT)


class ExtMetadataSetFormatTest(ATSiteTestCase):

    value = "fooooo"
    filename = 'foo.txt'

    def afterSetUp(self):
        portal = self.portal

        # to enable overrideDiscussionFor
        self.setRoles(['Manager'])

        parent = mkDummyInContext(DummyFolder, oid='parent', context=portal, schema=None)
        self._parent = parent

        # create dummy
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

    def testDiscussionEditAccessorDoesConversions(self):
        # Use a DDocument because the dummy is too dumb for this
        self.folder.invokeFactory('DDocument','bogus_item')
        dummy = self.folder.bogus_item
        # Set Allow discussion
        dummy.allowDiscussion(True)
        self.failUnless(dummy.isDiscussable())
        self.assertEqual(dummy.editIsDiscussable(), True)
        dummy.allowDiscussion(None)
        self.assertEqual(dummy.editIsDiscussable(), False)
        self.assertEqual(dummy.rawIsDiscussable(), None)
        dummy.allowDiscussion(False)
        self.failIf(dummy.isDiscussable())
        self.assertEqual(dummy.editIsDiscussable(), False)

    def testDiscussionOverride(self):
        # Make sure that if allowed_discussion is set on the class
        # we can still use allowDiscussion to override it.
        #
        # Use a DDocument because the dummy is too dumb for this
        # but temporarily set an allow_discussion attribute on the class.
        from Products.Archetypes.examples.DDocument import DDocument
        DDocument.allow_discussion = True
        self.folder.invokeFactory('DDocument','bogus_item')
        dummy = self.folder.bogus_item
        dummy.allowDiscussion(None)
        # clear our bogus attribute
        del DDocument.allow_discussion


class TimeZoneTest(ATSiteTestCase):
    def _makeDummyContent(self, name):
        return mkDummyInContext(
            klass=Dummy, oid=name, context=self.portal, schema=schema)

    def test_Date_with_explicit_timezone(self):
        item = self._makeDummyContent('item')
        item.setModificationDate(DateTime('2007-01-01T12:00:00Z'))
        self.assertEqual(item.Date('US/Eastern'),
                         '2007-01-01T07:00:00-05:00')

    def test_CreationDate_with_explicit_timezone(self):
        item = self._makeDummyContent('item')
        item.setCreationDate(DateTime('2007-01-01T12:00:00Z'))
        self.assertEqual(item.CreationDate('US/Eastern'),
                         '2007-01-01T07:00:00-05:00')

    def test_ModificationDate_with_explicit_timezone(self):
        item = self._makeDummyContent('item')
        item.setModificationDate(DateTime('2007-01-01T12:00:00Z'))
        self.assertEqual(item.ModificationDate('US/Eastern'),
                         '2007-01-01T07:00:00-05:00')

    def test_EffectiveDate_with_explicit_timezone(self):
        item = self._makeDummyContent('item')
        item.setEffectiveDate(DateTime('2007-01-01T12:00:00Z'))
        self.assertEqual(item.EffectiveDate('US/Eastern'),
                         '2007-01-01T07:00:00-05:00')

    def test_ExpirationDate_with_explicit_timezone(self):
        item = self._makeDummyContent('item')
        item.setExpirationDate(DateTime('2007-01-01T12:00:00Z'))
        self.assertEqual(item.ExpirationDate('US/Eastern'),
                         '2007-01-01T07:00:00-05:00')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ExtensibleMetadataTest))
    suite.addTest(makeSuite(ExtMetadataContextTest))
    suite.addTest(makeSuite(ExtMetadataDefaultLanguageTest))
    suite.addTest(makeSuite(ExtMetadataSetFormatTest))
    suite.addTest(makeSuite(TimeZoneTest))
    return suite
