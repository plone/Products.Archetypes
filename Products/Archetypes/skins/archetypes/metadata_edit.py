## Script (Python) "metadata_edit"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=id=''

context.processForm(data=0, metadata=1)

return ('success', context, {'portal_status_message':context.REQUEST.get('portal_status_message', 'Content changes saved.')})
