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

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase

# need this to initialize new BU for tests
from Products.Archetypes.tests.test_classgen import Dummy

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME, LANGUAGE_DEFAULT
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.CMFCore import permissions
from Products.Archetypes.ExtensibleMetadata import FLOOR_DATE
from Products.Archetypes.ExtensibleMetadata import CEILING_DATE
from Products.validation import ValidationChain

from DateTime import DateTime

Dummy.schema = BaseSchema

EmptyValidator = ValidationChain('isEmpty')
EmptyValidator.appendSufficient('isEmpty')

class BaseSchemaTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        registerType(Dummy, 'Archetypes')
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        portal = self.portal
        dummy = Dummy(oid='dummy')
        # put dummy in context of portal
        dummy = dummy.__of__(portal)
        portal.dummy = dummy

        dummy.initializeArchetype()
        self._dummy = dummy


    def test_id(self):
        dummy = self._dummy
        field = dummy.getField('id')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == None)
        self.failUnless(field.searchable == 0)
        self.failUnless(field.vocabulary == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 0)
        self.failUnless(field.accessor == 'getId')
        self.failUnless(field.mutator == 'setId')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'veVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'string')
        self.failUnless(isinstance(field.storage, AttributeStorage))
        self.failUnless(field.getLayerImpl('storage') == AttributeStorage())
        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, IdWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_title(self):
        dummy = self._dummy
        field = dummy.getField('title')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 1)
        self.failUnless(field.default == '')
        self.failUnless(field.searchable == 1)
        self.failUnless(field.vocabulary == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 0)
        self.failUnless(field.accessor == 'Title')
        self.failUnless(field.mutator == 'setTitle')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'veVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'string')
        self.failUnless(isinstance(field.storage, AttributeStorage))
        self.failUnless(field.getLayerImpl('storage') == AttributeStorage())
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, StringWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    ### Metadata Properties

    def test_allowdiscussion(self):
        dummy = self._dummy
        field = dummy.getField('allowDiscussion')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == None)
        self.failUnless(field.searchable == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'isDiscussable')
        self.failUnless(field.mutator == 'allowDiscussion')
        self.failUnless(field.edit_accessor == 'editIsDiscussable')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'boolean')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, BooleanWidget))

    def test_subject(self):
        dummy = self._dummy
        field = dummy.getField('subject')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == ())
        self.failUnless(field.searchable == 1)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 1)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Subject')
        self.failUnless(field.mutator == 'setSubject')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'lines')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, KeywordWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_description(self):
        dummy = self._dummy
        field = dummy.getField('description')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == '')
        self.failUnless(field.searchable == 1)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Description')
        self.failUnless(field.mutator == 'setDescription')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'text')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_contributors(self):
        dummy = self._dummy
        field = dummy.getField('contributors')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == ())
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Contributors')
        self.failUnless(field.mutator == 'setContributors')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'lines')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, LinesWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_effectivedate(self):
        dummy = self._dummy
        field = dummy.getField('effectiveDate')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnlessEqual(field.default, None)
        self.failUnlessEqual(dummy.effective(), FLOOR_DATE)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.mutator == 'setEffectiveDate')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'datetime')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, CalendarWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_expirationdate(self):
        dummy = self._dummy
        field = dummy.getField('expirationDate')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnlessEqual(field.default, None)
        self.failUnlessEqual(dummy.expires(), CEILING_DATE)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.mutator == 'setExpirationDate')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'datetime')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, CalendarWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_language(self):
        default=LANGUAGE_DEFAULT
        dummy = self._dummy
        field = dummy.getField('language')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == LANGUAGE_DEFAULT)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == 'languages')
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Language')
        self.failUnless(field.mutator == 'setLanguage')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'string')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, LanguageWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(vocab == dummy.languages())

    def test_rights(self):
        dummy = self._dummy
        field = dummy.getField('rights')

        self.failUnless(ILayerContainer.providedBy(field))
        self.failUnless(field.required == 0)
        self.failUnless(field.default == '')
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Rights')
        self.failUnless(field.mutator == 'setRights')
        self.failUnless(field.read_permission == permissions.View)
        self.failUnless(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'text')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.getLayerImpl('storage') == MetadataStorage())
        self.failUnless(field.validators == EmptyValidator)
        self.failUnless(isinstance(field.widget, TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    # metadata utility accessors (DublinCore)
    def test_EffectiveDate(self):
        dummy = self._dummy
        self.failUnless(dummy.EffectiveDate() == 'None')
        now = DateTime()
        dummy.setEffectiveDate(now)
        self.failUnless(dummy.EffectiveDate() == now.ISO8601())

    def test_ExpiresDate(self):
        dummy = self._dummy
        self.failUnless(dummy.ExpirationDate() == 'None')
        now = DateTime()
        dummy.setExpirationDate(now)
        self.failUnless(dummy.ExpirationDate() == now.ISO8601())

    def test_Date(self):
        dummy = self._dummy
        self.failUnless(isinstance(dummy.Date(), str))
        dummy.setEffectiveDate(DateTime())
        self.failUnless(isinstance(dummy.Date(), str))

    def test_contentEffective(self):
        dummy = self._dummy
        now = DateTime()
        then = DateTime() + 1000
        self.failUnless(dummy.contentEffective(now))
        dummy.setExpirationDate(then)
        self.failUnless(dummy.contentEffective(now))
        dummy.setEffectiveDate(now)
        self.failUnless(dummy.contentEffective(now))
        dummy.setEffectiveDate(then)
        self.failIf(dummy.contentEffective(now))

    def test_contentExpired(self):
        dummy = self._dummy
        now = DateTime()
        then = DateTime() + 1000
        self.failIf(dummy.contentExpired())
        dummy.setExpirationDate(then)
        self.failIf(dummy.contentExpired())
        dummy.setExpirationDate(now)
        self.failUnless(dummy.contentExpired())

    def testRespectDaylightSavingTime(self):
        """ When saving dates, the date's timezone with Daylight Saving Time
            has to be respected.
            See Products.Archetypes.Field.DateTimeField.set
        """
        dummy = self._dummy
        dummy.setEffectiveDate('2010-01-01 10:00 Europe/Belgrade')
        dummy.setExpirationDate('2010-06-01 10:00 Europe/Belgrade')
        self.failUnless(dummy.effective_date.tzoffset() == 3600)
        self.failUnless(dummy.expiration_date.tzoffset() == 7200)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(BaseSchemaTest))
    return suite
