## Script (Python) "content_edit"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=id=''

context.processForm()

return ('success', context, {'portal_status_message':context.REQUEST.get('portal_status_message', 'Content changes saved.')})
