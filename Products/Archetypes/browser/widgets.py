from Acquisition import aq_inner
from Products.Five import BrowserView


class SelectionWidget(BrowserView):
    """View used in Archetypes language and selection widget."""

    def getSelected(self, vocab, value):
        context = aq_inner(self.context)

        site_charset = context.getCharset()

        def lazyVocab(vocab):
            for key in vocab:
                # vocabulary keys can only be strings or integers
                if isinstance(key, str):
                    key = key.decode(site_charset)
                yield key

        values = {}
        # we compute a dictonary of {oldvalue : encodedvalue} items, so we can
        # return the exact oldvalue we got for comparision in the template but can
        # compare the unicode values against the vocabulary
        if isinstance(value, tuple) or isinstance(value, list):
            for v in value:
                new = v
                if isinstance(v, int):
                    v = str(v)
                elif isinstance(v, str):
                    new = v.decode(site_charset)
                values[new] = v
        else:
            if isinstance(value, str):
                new = value.decode(site_charset)
            else:
                new = str(value)
            values[new] = value

        selected = []
        for v in values:
            if v in lazyVocab(vocab):
                selected.append(values[v])

        return selected
