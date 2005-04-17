## Script (Python) "download"
##title=Download a file keeping the original uploaded filename
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
REQUEST  = context.REQUEST
RESPONSE = REQUEST.RESPONSE
if hasattr(context.aq_explicit, 'data'):
    # handle OFS.Image.File and OFS.Image.Image
    data = str(context.data)
else:
    data = str(context)
RESPONSE.setHeader('Content-Disposition',
                   'attachment; filename=%s' % context.getFilename())
RESPONSE.setHeader('Content-Type', context.getContentType())
RESPONSE.setHeader('Content-Length', context.get_size())
RESPONSE.write(data)
