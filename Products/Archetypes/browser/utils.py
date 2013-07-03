from zope.interface import implements
from Products.Five import BrowserView
from Products.Archetypes.interfaces.utils import IUtils
from zope.i18n import translate
from zope.i18nmessageid import Message


class Utils(BrowserView):
    implements(IUtils)

    def translate(self, vocab, value, widget=None):
        domain = 'plone'
        context = self.context
        if isinstance(value, basestring):
            value = [value]
        if widget:
            custom_domain = getattr(widget, 'i18n_domain', None)
            if custom_domain:
                domain = custom_domain
        def _(value):
            return translate(value,
                             domain=domain,
                             context=self.request)
        if value:
            nvalues = []
            for v in value:
                if not v:
                    continue
                v_encoded = context.unicodeEncode(v)
                vocab_value = vocab.getValue(v_encoded, v)
                # avoid UnicodeDecodeError if value contains special chars
                if not isinstance(vocab_value, unicode):
                    vocab_value = unicode(vocab_value, 'utf-8')
                # translate explicitly
                vocab_value = _(vocab_value)
                nvalues.append(vocab_value)
            value =  ', '.join(nvalues)
        return value
