from unittest import TestSuite, makeSuite

from zope.component import getMultiAdapter

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.atapi import DisplayList


class UtilsMethodsTests(ATSiteTestCase):
    """Test the different methods in browser.utils view."""

    def test_translate_vocab_with_special_chars(self):
        vocab = DisplayList((('Sp\xc3\xa9cial char key', 'Sp\xc3\xa9cial char value'),
                             ('normal_key', 'With sp\xc3\xa9cial char'), ))
        utilsView = getMultiAdapter((self.portal, self.portal.REQUEST), name='at_utils')
        # Note that due to the test setup, the result is expected to
        # be u'[[domain][translation]]'.
        self.assertEqual(utilsView.translate(vocab, value='Sp\xc3\xa9cial char key'),
                         u'[[plone][Sp\xe9cial char value]]')
        self.assertEqual(utilsView.translate(vocab, value='normal_key'),
                         u'[[plone][With sp\xe9cial char]]')


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(UtilsMethodsTests))
    return suite
