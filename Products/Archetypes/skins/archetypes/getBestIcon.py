## Script (Python) "getBestIcon"
##title=Find most specific icon for an (sub)object
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath

from Products.Archetypes.debug import log
try:
    mtr = context.mimetypes_registry
    mti = mtr.lookup(context.getContentType())[0]
    icon = mti.icon_path
except Exception, E:
    icon = context.getIcon()

return icon
