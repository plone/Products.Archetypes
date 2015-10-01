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

# need this to initialize new BU for tests
from Products.Archetypes.tests.test_classgen import Dummy

from Products.Archetypes import atapi
from Products.Archetypes.config import PKG_NAME, LANGUAGE_DEFAULT
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.CMFCore import permissions
from Products.Archetypes.ExtensibleMetadata import FLOOR_DATE
from Products.Archetypes.ExtensibleMetadata import CEILING_DATE
from Products.validation import ValidationChain

from DateTime import DateTime

Dummy.schema = atapi.BaseSchema

EmptyValidator = ValidationChain('isEmpty')
EmptyValidator.appendSufficient('isEmpty')


class BaseSchemaTest(ATSiteTestCase):

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        atapi.registerType(Dummy, 'Archetypes')
        content_types, constructors, ftis = atapi.process_types(
            atapi.listTypes(), PKG_NAME)
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

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == None)
        self.assertTrue(field.searchable == 0)
        self.assertTrue(field.vocabulary == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 0)
        self.assertTrue(field.accessor == 'getId')
        self.assertTrue(field.mutator == 'setId')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'veVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'string')
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.AttributeStorage())
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.IdWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_title(self):
        dummy = self._dummy
        field = dummy.getField('title')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1)
        self.assertTrue(field.default == '')
        self.assertTrue(field.searchable == 1)
        self.assertTrue(field.vocabulary == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 0)
        self.assertTrue(field.accessor == 'Title')
        self.assertTrue(field.mutator == 'setTitle')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'veVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'string')
        self.assertTrue(isinstance(field.storage, atapi.AttributeStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.AttributeStorage())
        self.assertTrue(field.validators == ())
        self.assertTrue(isinstance(field.widget, atapi.StringWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    # Metadata Properties

    def test_allowdiscussion(self):
        dummy = self._dummy
        field = dummy.getField('allowDiscussion')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == None)
        self.assertTrue(field.searchable == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'isDiscussable')
        self.assertTrue(field.mutator == 'allowDiscussion')
        self.assertTrue(field.edit_accessor == 'editIsDiscussable')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'boolean')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.BooleanWidget))

    def test_subject(self):
        dummy = self._dummy
        field = dummy.getField('subject')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == ())
        self.assertTrue(field.searchable == 1)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 1)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'Subject')
        self.assertTrue(field.mutator == 'setSubject')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'lines')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.TagsWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_description(self):
        dummy = self._dummy
        field = dummy.getField('description')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == '')
        self.assertTrue(field.searchable == 1)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'Description')
        self.assertTrue(field.mutator == 'setDescription')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'text')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_contributors(self):
        dummy = self._dummy
        field = dummy.getField('contributors')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == ())
        self.assertTrue(field.searchable == 0)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'Contributors')
        self.assertTrue(field.mutator == 'setContributors')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'lines')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.AjaxSelectWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_effectivedate(self):
        dummy = self._dummy
        field = dummy.getField('effectiveDate')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertEqual(field.default, None)
        self.assertEqual(dummy.effective(), FLOOR_DATE)
        self.assertTrue(field.searchable == 0)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.mutator == 'setEffectiveDate')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'datetime')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.DatetimeWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_expirationdate(self):
        dummy = self._dummy
        field = dummy.getField('expirationDate')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertEqual(field.default, None)
        self.assertEqual(dummy.expires(), CEILING_DATE)
        self.assertTrue(field.searchable == 0)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.mutator == 'setExpirationDate')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'datetime')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.DatetimeWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    def test_language(self):
        dummy = self._dummy
        field = dummy.getField('language')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == LANGUAGE_DEFAULT)
        self.assertTrue(field.searchable == 0)
        vocab = field.vocabulary
        self.assertTrue(vocab == 'languages')
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'Language')
        self.assertTrue(field.mutator == 'setLanguage')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'string')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.SelectWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(vocab == dummy.languages())

    def test_rights(self):
        dummy = self._dummy
        field = dummy.getField('rights')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0)
        self.assertTrue(field.default == '')
        self.assertTrue(field.searchable == 0)
        vocab = field.vocabulary
        self.assertTrue(vocab == ())
        self.assertTrue(field.enforceVocabulary == 0)
        self.assertTrue(field.multiValued == 0)
        self.assertTrue(field.isMetadata == 1)
        self.assertTrue(field.accessor == 'Rights')
        self.assertTrue(field.mutator == 'setRights')
        self.assertTrue(field.read_permission == permissions.View)
        self.assertTrue(field.write_permission ==
                        permissions.ModifyPortalContent)
        self.assertTrue(field.generateMode == 'mVc')
        self.assertTrue(field.force == '')
        self.assertTrue(field.type == 'text')
        self.assertTrue(isinstance(field.storage, atapi.MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage')
                        == atapi.MetadataStorage())
        self.assertTrue(field.validators == EmptyValidator)
        self.assertTrue(isinstance(field.widget, atapi.TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList))
        self.assertTrue(tuple(vocab) == ())

    # metadata utility accessors (DublinCore)
    def test_EffectiveDate(self):
        dummy = self._dummy
        self.assertTrue(dummy.EffectiveDate() == 'None')
        now = DateTime()
        dummy.setEffectiveDate(now)
        self.assertTrue(dummy.EffectiveDate() == now.ISO8601())

    def test_ExpiresDate(self):
        dummy = self._dummy
        self.assertTrue(dummy.ExpirationDate() == 'None')
        now = DateTime()
        dummy.setExpirationDate(now)
        self.assertTrue(dummy.ExpirationDate() == now.ISO8601())

    def test_Date(self):
        dummy = self._dummy
        self.assertTrue(isinstance(dummy.Date(), str))
        dummy.setEffectiveDate(DateTime())
        self.assertTrue(isinstance(dummy.Date(), str))

    def test_contentEffective(self):
        dummy = self._dummy
        now = DateTime()
        then = DateTime() + 1000
        self.assertTrue(dummy.contentEffective(now))
        dummy.setExpirationDate(then)
        self.assertTrue(dummy.contentEffective(now))
        dummy.setEffectiveDate(now)
        self.assertTrue(dummy.contentEffective(now))
        dummy.setEffectiveDate(then)
        self.assertFalse(dummy.contentEffective(now))

    def test_contentExpired(self):
        dummy = self._dummy
        now = DateTime()
        then = DateTime() + 1000
        self.assertFalse(dummy.contentExpired())
        dummy.setExpirationDate(then)
        self.assertFalse(dummy.contentExpired())
        dummy.setExpirationDate(now)
        self.assertTrue(dummy.contentExpired())

    def testRespectDaylightSavingTime(self):
        """ When saving dates, the date's timezone with Daylight Saving Time
            has to be respected.
            See Products.Archetypes.Field.DateTimeField.set
        """
        dummy = self._dummy
        dummy.setEffectiveDate('2010-01-01 10:00 Europe/Belgrade')
        dummy.setExpirationDate('2010-06-01 10:00 Europe/Belgrade')
        self.assertTrue(dummy.effective_date.tzoffset() == 3600)
        self.assertTrue(dummy.expiration_date.tzoffset() == 7200)
