from zope.interface import implements
from Products.Five import BrowserView
from Products.Archetypes.interfaces.utils import IUtils
from zope.i18n import translate


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
                if not v: continue
                vocab_value = vocab.getValue(
                    context.unicodeEncode(v),
                    context.unicodeEncode(v))
                # be sure not to have already translated
                # the text
                trans_value = _(v)
                if vocab_value != trans_value:
                    vocab_value = trans_value
                nvalues.append(vocab_value)
            value =  ', '.join(nvalues)
        return value

