## Script (Python) "unicodeEncode"
##title=Return an encoded string using the site charset
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=value, site_charset=None

if site_charset is None:
    site_charset = context.getCharset()

# Recursively deal with sequences
if (same_type(value, ()) or same_type(value, [])):
    encoded = [context.unicodeEncode(v) for v in value]
    if same_type(value, ()):
        encoded = tuple(encoded)
    return encoded

if not (same_type(value, '') or same_type(value, u'')):
    value = str(value)

if same_type(value, ''):
    for charset in [site_charset, 'latin-1', 'utf-8']:
        try:
            value = unicode(value, charset)
            break
        except UnicodeError:
            pass
    # that should help debugging unicode problem
    # remove it if you feel not
    else:
        raise UnicodeError('Unable to decode %s' % value)

# don't try to catch unicode error here
# if one occurs, that means the site charset must be changed !
return value.encode(site_charset)
