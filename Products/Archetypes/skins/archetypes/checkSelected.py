## Script (Python) "Check Selected"
##title=Check if a field should be 'selected' based on value and vocabulary
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=item, value, contenttypes=0
from Products.CMFCore.utils import getToolByName

# get site encoding
proptool = getToolByName(context, 'portal_properties')
enc = proptool.site_properties.default_charset
##if enc.lower() == 'utf8':
##    enc = 'utf-8'

if same_type(item, 0): item = str(item)
if same_type(value, 0): value = str(value)

if same_type(item, ''): 
    try:
        item = unicode(item, enc)
    except UnicodeDecodeError:
        try:
            item = unicode(item, 'latin1')
        except UnicodeDecodeError:
            pass

if same_type(value , ''): 
    try:
        value = unicode(value, enc)
    except UnicodeDecodeError:
        try:
            value = unicode(value, 'latin1')
        except UnicodeDecodeError:
            pass

# map from mimetypes used in allowable_content_types to mimetypes that are stored
# in the base unit
mapping = {
    'text/x-python' : 'text/python-source',
    'text/restructured': 'text/x-rst',
}

if contenttypes:
    item = mapping.get(item, item)

if value is not None and \
   value == item or \
   unicode(repr(value)) == unicode(repr(item)):
    return 1

try:
    # Maybe string?
    value.capitalize()
except AttributeError:
    # Maybe list?
    try:
        for v in value:
            if unicode(repr(item)) == unicode(repr(v)):
                return 1
    except TypeError:
        pass

return not not unicode(repr(value)) == unicode(repr(item))
