from zope.component import getMultiAdapter

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.atapi import IntDisplayList


class UtilsMethodsTests(ATSiteTestCase):
    """Test the different methods in browser.utils view."""

    def test_translate_vocab_with_special_chars(self):
        vocab = DisplayList((('Sp\xc3\xa9cial char key', 'Sp\xc3\xa9cial char value'),
                             ('normal_key', 'With sp\xc3\xa9cial char'), ))
        utilsView = getMultiAdapter(
            (self.portal, self.portal.REQUEST), name='at_utils')
        # Note that due to the test setup, the result is expected to
        # be u'[[domain][translation]]'.
        self.assertEqual(utilsView.translate(vocab, value='Sp\xc3\xa9cial char key'),
                         u'[[plone][Sp\xe9cial char value]]')
        self.assertEqual(utilsView.translate(vocab, value='normal_key'),
                         u'[[plone][With sp\xe9cial char]]')
        # Try with unicode as input value
        self.assertEqual(utilsView.translate(vocab, value=u'Sp\xe9cial char key'),
                         u'[[plone][Sp\xe9cial char value]]')
        self.assertEqual(utilsView.translate(vocab, value=u'normal_key'),
                         u'[[plone][With sp\xe9cial char]]')

    def test_translate_integer_display_list(self):
        vocab = IntDisplayList(((1, 'Sp\xc3\xa9cial char value'),
                                (2, 'two'),
                                (3, 42), ))
        utilsView = getMultiAdapter(
            (self.portal, self.portal.REQUEST), name='at_utils')
        self.assertEqual(utilsView.translate(vocab, value=1),
                         u'[[plone][Sp\xe9cial char value]]')
        self.assertEqual(utilsView.translate(vocab, value=2),
                         u'[[plone][two]]')
        self.assertEqual(utilsView.translate(vocab, value=3),
                         u'[[plone][42]]')

    def test_translate_empty(self):
        vocab = DisplayList((('one', 'One'),
                             ('two', 'Two'), ))
        utilsView = getMultiAdapter(
            (self.portal, self.portal.REQUEST), name='at_utils')
        self.assertEqual(utilsView.translate(vocab, value=''), u'')
        self.assertEqual(utilsView.translate(vocab, value=None), u'')
        self.assertEqual(utilsView.translate(vocab, value=[]), u'')
        self.assertEqual(utilsView.translate(vocab, value=()), u'')
        self.assertEqual(utilsView.translate(vocab, value=set()), u'')
