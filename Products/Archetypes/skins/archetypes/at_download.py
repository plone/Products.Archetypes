## Script (Python) "download"
##title=Download a file keeping the original uploaded filename
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
REQUEST  = context.REQUEST
RESPONSE = REQUEST.RESPONSE

filename = getattr(context, 'filename', context.getId())
RESPONSE.setHeader('Content-Disposition',
                   'attachment; filename=%s' % filename)

if hasattr(context.aq_explicit, 'data'):
    # handle OFS.Image.File and OFS.Image.Image
    return context.index_html(REQUEST, RESPONSE)
else:
    data = str(context)

RESPONSE.setHeader('Content-Type', context.getContentType())
RESPONSE.setHeader('Content-Length', context.get_size())
RESPONSE.write(data)
