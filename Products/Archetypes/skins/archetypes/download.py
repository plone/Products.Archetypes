## Script (Python) "download"
##title=Download a file keeping the original uploaded filename
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
RESPONSE = context.REQUEST.RESPONSE
RESPONSE.setHeader('Content-Disposition',
                   'attachment; filename=%s' % context.filename)
RESPONSE.setHeader('Content-Type', context.getContentType())
RESPONSE.setHeader('Content-Length', context.get_size())
RESPONSE.write(context.data)
