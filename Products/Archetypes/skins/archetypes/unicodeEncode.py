## Script (Python) "unicodeEncode"
##title=Test if a unicode string is in a unicode list
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=value

charset = context.portal_properties.site_properties.default_charset
charsets = [charset, 'ascii', 'latin-1', 'utf-8']

for charset in charsets:
    try:
        value = unicode(value, charset).encode(charset)
    except UnicodeError:
        pass
    else:
        break

return value
