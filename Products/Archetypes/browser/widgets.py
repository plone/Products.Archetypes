from Acquisition import aq_inner
from Products.Five import BrowserView


# map from mimetypes used in allowable_content_types to mimetypes that are stored
# in the base unit
MIMETYPES_MAPPING = {
    'text/x-python' : 'text/python-source',
    'text/restructured': 'text/x-rst',
}


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


class TextareaWidget(BrowserView):
    """View used in Archetypes textarea widget."""

    def getSelected(self, mimetypes, contenttype):
        # An object can have only one contenttype at a time and mimetypes
        # are limited to ASCII-only characters. We already assumed to get all
        # values in all lowercase, so we don't do any case-juggling.

        contenttype = MIMETYPES_MAPPING.get(contenttype, contenttype)

        if contenttype in mimetypes:
            return (contenttype, )

        return ()

    def lookupMime(self, name):
        context = aq_inner(self.context)
        mimetool = context.mimetypes_registry
        mimetypes = mimetool.lookup(name)
        if len(mimetypes):
            return mimetypes[0].name()
        else:
            return name
