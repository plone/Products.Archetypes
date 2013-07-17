## Script (Python) "at_download"
##title=Download a file keeping the original uploaded filename
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath

if traverse_subpath:
    field = context.getWrappedField(traverse_subpath[0])
else:
    field = context.getPrimaryField()
if not field.checkPermission('r', context):
    from zExceptions import Unauthorized
    raise Unauthorized('Field %s requires %s permission' % (field, field.read_permission))
if not hasattr(field, 'download'):
    from zExceptions import NotFound
    raise NotFound
return field.download(context)
