## Script (Python) "validate_metadata"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##
errors = {}
errors = context.validate(REQUEST=context.REQUEST, errors=errors, data=0, metadata=1)

## TODO: Update to use ScriptStatus Object
if errors:
    return ('failure', errors, {'portal_status_message':'Please correct the indicated errors.'})
else:
    return ('success', errors, {'portal_status_message':'Your changes have been saved.'})
