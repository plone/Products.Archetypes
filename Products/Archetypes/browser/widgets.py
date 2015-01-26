from Acquisition import aq_inner
from Products.Five import BrowserView


# map from mimetypes used in allowable_content_types to mimetypes that
# are stored in the base unit
MIMETYPES_MAPPING = {
    'text/x-python': 'text/python-source',
    'text/restructured': 'text/x-rst',
}


class SelectionWidget(BrowserView):
    """View used in Archetypes language and selection widget.

    We start with a browser view for this widget.  We use a test
    request and some very simple content to initialize it.

    >>> from zope.publisher.browser import TestRequest
    >>> class SimpleContent(object):
    ...     def getCharset(self):
    ...         return 'utf-8'
    >>> widget = SelectionWidget(SimpleContent(), TestRequest())

    Test with a simple vocabulary

    >>> vocab = ('a', 'b', 'c')
    >>> widget.getSelected(vocab, 'a')
    ['a']
    >>> widget.getSelected(vocab, 'A')
    []
    >>> widget.getSelected(vocab, 'd')
    []

    >>> vocab = ('b', 'a', 'd', 'c')
    >>> widget.getSelected(vocab, ('b', 'c'))
    ['b', 'c']

    Test with a DisplayList

    >>> from Products.Archetypes.utils import DisplayList
    >>> friends = DisplayList([('Monty Python', u'monty'),
    ...                        (u'Guido van Rossum', u'guido')])
    >>> widget.getSelected(friends, 'monty')
    []
    >>> widget.getSelected(friends, u'guido')
    []
    >>> widget.getSelected(friends, 'Spanish Inquisition')
    []

    getSelected is used to get a list of selected vocabulary items.
    In the widget, we repeat on the vocabulary, comparing
    its values with those returned by getSelected. So,
    we always return the same encoding as in the vocabulary.

    >>> widget.getSelected(friends, u'Monty Python')
    ['Monty Python']
    >>> widget.getSelected(friends, 'Monty Python')
    ['Monty Python']
    >>> widget.getSelected(friends, u'Guido van Rossum')
    [u'Guido van Rossum']
    >>> widget.getSelected(friends, 'Guido van Rossum')
    [u'Guido van Rossum']

    Test with an IntDisplayList:

    >>> from Products.Archetypes.utils import IntDisplayList
    >>> quarter_vocabulary = IntDisplayList([(0, '0'), (15, '15'),
    ...                                      (30, '30'), (45, '45')])
    >>> widget.getSelected(quarter_vocabulary, 5)
    []
    >>> widget.getSelected(quarter_vocabulary, 0)
    [0]
    >>> widget.getSelected(quarter_vocabulary, 15)
    [15]
    >>> widget.getSelected(quarter_vocabulary, '15')
    [15]
    >>> widget.getSelected(quarter_vocabulary, 'wrongdata')
    []
    >>> widget.getSelected(quarter_vocabulary, None)
    []

    """

    def getSelected(self, vocab, value):

        context = aq_inner(self.context)

        site_charset = context.getCharset()

        # compile a dictionary from the vocabulary of
        # items in {encodedvalue : originalvalue} format
        vocabKeys = {}
        # Also keep a list of integer keys, if available.
        integerKeys = {}
        for key in vocab:
            # vocabulary keys can only be strings or integers
            if isinstance(key, str):
                vocabKeys[key.decode(site_charset)] = key
            else:
                vocabKeys[key] = key
                integerKeys[key] = key

        # compile a dictonary of {encodedvalue : oldvalue} items
        # from value -- which may be a sequence, string or integer.
        pos = 0
        values = {}
        if isinstance(value, tuple) or isinstance(value, list):
            for v in value:
                new = v
                if isinstance(v, int):
                    v = str(v)
                elif isinstance(v, str):
                    new = v.decode(site_charset)
                values[(new, pos)] = v
                pos += 1
        else:
            if isinstance(value, str):
                new = value.decode(site_charset)
            elif isinstance(value, int):
                new = value
            else:
                new = str(value)
            values[(new, pos)] = value

        # now, build a list of the vocabulary keys
        # in their original charsets.
        selected = []
        for v, pos in values:
            ov = vocabKeys.get(v)
            if ov is not None:
                selected.append((pos, ov))
            elif integerKeys:
                # Submitting a string '5' where the vocabulary has
                # only integer keys works fine when the edit succeeds.
                # But when the edit form gets redisplayed (e.g. due to
                # a missing required field), the string '5' means
                # nothing is selected here, so you loose what you
                # filled in.  This gets fixed right here.
                try:
                    int_value = int(value)
                except (ValueError, TypeError):
                    continue
                ov = integerKeys.get(int_value)
                if ov is not None:
                    selected.append((pos, ov))
        selected.sort()
        return [v for pos, v in selected]


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


class PatternsWidgetMacros(BrowserView):

    @property
    def macros(self):
        return self.index.macros
