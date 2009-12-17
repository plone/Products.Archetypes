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
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName


Dummy.schema = BaseSchema

class LanguageVocabularyTest(ATSiteTestCase):

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

    def test_no_combined_codes(self):
        tool = getToolByName(self.portal,'portal_languages')
        defaultLanguage = 'en'
        supportedLanguages = ['en','de','no']
        tool.manage_setLanguageSettings(defaultLanguage,
                                        supportedLanguages,
                                        setUseCombinedLanguageCodes=False)
        dummy = self._dummy
        field = dummy.getField('language')
        vocab = field.Vocabulary(dummy)
        self.failIf('pt-br' in vocab.keys())
    
    def test_combined_codes(self):
        tool = getToolByName(self.portal,'portal_languages')
        defaultLanguage = 'pt-br'
        supportedLanguages = ['pt-br','en','de','no']
        tool.manage_setLanguageSettings(defaultLanguage,
                                        supportedLanguages,
                                        setUseCombinedLanguageCodes=True)
        dummy = self._dummy
        field = dummy.getField('language')
        vocab = field.Vocabulary(dummy)
        self.failUnless('pt-br' in vocab.keys())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(LanguageVocabularyTest))
    return suite
