from zope.interface import implementer
from Products.Five import BrowserView
from Products.Archetypes.interfaces.utils import IUtils
from zope.i18n import translate


@implementer(IUtils)
class Utils(BrowserView):

    def translate(self, vocab, value, widget=None):
        """Translate an input value from a vocabulary.

        - vocab is a vocabulary, for example a DisplayList or IntDisplayList

        - 'value' is meant as 'input value' and should have been
          called 'key', really, because we will lookup this key in the
          vocabulary, which should give us a value as answer.  When no
          such value is known, we take the original input value.  This
          gets translated.

        - By passing a widget with a i18n_domain attribute, we use
          that as the translation domain.  The default is 'plone'.

        Supported input values are at least: string, integer, list and
        tuple.  When there are multiple values, we iterate over them.
        """
        domain = 'plone'
        # Make sure value is an iterable.  There are really too many
        # iterable and non-iterable types (and half-iterable like
        # strings, which we definitely do not want to iterate over) so
        # we check the __iter__ attribute:
        if not hasattr(value, '__iter__'):
            value = [value]
        if widget:
            custom_domain = getattr(widget, 'i18n_domain', None)
            if custom_domain:
                domain = custom_domain

        def _(value):
            return translate(value,
                             domain=domain,
                             context=self.request)
        nvalues = []
        for v in value:
            if not v:
                continue
            original = v
            if isinstance(v, unicode):
                v = v.encode('utf-8')
            # Get the value with key v from the vocabulary,
            # falling back to the original input value.
            vocab_value = vocab.getValue(v, original)
            if not isinstance(vocab_value, basestring):
                # May be an integer.
                vocab_value = str(vocab_value)
            elif not isinstance(vocab_value, unicode):
                # avoid UnicodeDecodeError if value contains special chars
                vocab_value = unicode(vocab_value, 'utf-8')
            # translate explicitly
            vocab_value = _(vocab_value)
            nvalues.append(vocab_value)
        value = ', '.join(nvalues)
        return value
