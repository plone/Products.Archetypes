## Script (Python) "Check Selected"
##title=Check if a field should be 'selected' based on value and vocabulary
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=item, value, contenttypes=0

site_charset = context.getCharset()
item = context.unicodeEncode(item, site_charset=site_charset)
value = context.unicodeEncode(value, site_charset=site_charset)

# map from mimetypes used in allowable_content_types to mimetypes that are stored
# in the base unit
mapping = {
    'text/x-python': 'text/python-source',
    'text/restructured': 'text/x-rst',
}

if contenttypes:
    item = mapping.get(item, item)

uitem = unicode(repr(item))

if value is not None and \
   value == item or \
   unicode(repr(value)) == uitem:
    return 1

if isinstance(value, basestring):
    value.capitalize()

# Maybe list?
try:
    for v in value:
        if uitem == unicode(repr(v)):
            return 1
except TypeError:
    pass

return unicode(repr(value)) == uitem
