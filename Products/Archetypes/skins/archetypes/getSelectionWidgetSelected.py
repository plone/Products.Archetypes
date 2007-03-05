## Script (Python) "Get Selected"
##title=Returns the list of values of the field that should be 'selected' based on value and vocabulary
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=vocab, value

site_charset = context.getCharset()

keys = []
# vocabulary keys can only be strings or integers
for key in vocab.keys():
    if isinstance(key, str):
        key = key.decode(site_charset)
    keys.append(key)

values = {}
# we compute a dictonary of {oldvalue : encodedvalue} items, so we can
# return the exact oldvalue we got for comparision in the template but can
# compare the unicode values against the vocabulary
if isinstance(value, tuple) or same_type(value, []):
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
    if v in keys:
        selected.append(values[v])

return selected
