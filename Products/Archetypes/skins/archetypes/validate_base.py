## Script (Python) "validate_DDocument_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##
errors = {}
errors = context.validate(REQUEST=context.REQUEST, errors=errors)

## TODO: Update to use ScriptStatus Object
if errors:
    return ('failure', errors, {'portal_status_message':'Please correct the indicated errors.'})
else:
    return ('success', errors, {'portal_status_message':'Your changes have been saved.'})
