## Script (Python) "validate_base"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##
kwargs = context.REQUEST.form
if kwargs.has_key("setmaster"):
    if len(kwargs) != 3:
        return ('failure', {}, {'portal_status_message':
                                'You must select one language to set it as the master translation.'})
else:
    if kwargs.has_key(context.getMasterLanguage()):
        return ('failure', {}, {'portal_status_message': 'You can not delete the master translation'})

return ('success', {}, {'portal_status_message':'Your changes have been saved.'})
