from Products.CMFCore.utils import getToolByName

from Products.Archetypes.atapi import BaseSchema
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.atapi import registerType
from Products.Archetypes.atapi import process_types
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.test_classgen import Dummy

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
        tool = getToolByName(self.portal, 'portal_languages', None)
        defaultLanguage = 'en'
        supportedLanguages = ['en','de','no']
        if tool is not None:
            tool.manage_setLanguageSettings(defaultLanguage,
                                            supportedLanguages,
                                            setUseCombinedLanguageCodes=False)
        dummy = self._dummy
        field = dummy.getField('language')
        vocab = field.Vocabulary(dummy)
        self.failIf('pt-br' in vocab.keys())

    def test_combined_codes(self):
        tool = getToolByName(self.portal, 'portal_languages', None)
        defaultLanguage = 'pt-br'
        supportedLanguages = ['pt-br','en','de','no']
        if tool is not None:
            tool.manage_setLanguageSettings(defaultLanguage,
                                            supportedLanguages,
                                            setUseCombinedLanguageCodes=True)
        dummy = self._dummy
        field = dummy.getField('language')
        vocab = field.Vocabulary(dummy)
        if tool is None:
            self.failIf('pt-br' in vocab.keys())
        else:
            self.failUnless('pt-br' in vocab.keys())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(LanguageVocabularyTest))
    return suite
