## Script (Python) "at_isEditable"
##title=Check if an at object is editable
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fields

# the script is assuming that an object is editable if the given field list is
# not empty
if len(fields) == 0:
    from AccessControl import Unauthorized
    raise Unauthorized, context
