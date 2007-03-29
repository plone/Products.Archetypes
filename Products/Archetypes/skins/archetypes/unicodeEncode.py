## Script (Python) "unicodeEncode"
##title=Return an encoded string using the site charset
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=value, site_charset=None

# Recursively deal with sequences
tuplevalue = same_type(value, ())
if (tuplevalue or same_type(value, [])):
    encoded = [context.unicodeEncode(v) for v in value]
    if tuplevalue:
        encoded = tuple(encoded)
    return encoded

if not isinstance(value, basestring):
    value = str(value)

if site_charset is None:
    site_charset = context.getCharset()

if same_type(value, ''):
    value = unicode(value, site_charset)

# don't try to catch unicode error here
# if one occurs, that means the site charset must be changed !
return value.encode(site_charset)
