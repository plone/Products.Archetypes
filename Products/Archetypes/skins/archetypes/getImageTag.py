## Script (Python) "getImageTag"
##title=Get HTML tag for image field, with optional scale
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fieldName, scale = None

return context.getWrappedField(fieldName).tag(context, scale)
