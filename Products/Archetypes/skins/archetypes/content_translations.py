## Script (Python) "content_translations"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

REQUEST = context.REQUEST
context.manage_translations(REQUEST=REQUEST)
portal_status_message = REQUEST.get('portal_status_message', 'Content changes saved.')
return ('success', context, {'portal_status_message':portal_status_message})
