## Script (Python) "Check Selected"
##title=Check if a field should be 'selected' based on value and vocabulary
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=item, value

if value is not None and \
   unicode(str(value)) == unicode(str(item)):
    return 1

try:
    for v in value:
        if unicode(str(item)) == unicode(str(v)):
            return 1
except TypeError:
    return 0
