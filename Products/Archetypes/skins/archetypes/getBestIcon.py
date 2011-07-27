## Script (Python) "getBestIcon"
##title=Find most specific icon for an (sub)object
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
from Products.CMFCore.utils import getToolByName
from zExceptions import NotFound
from Products.MimetypesRegistry.common import MimeTypeException

mtr = getToolByName(context, 'mimetypes_registry', None)
if mtr is None:
    return context.getIcon()

try:
    lookup = mtr.lookup(context.getContentType())
except MimeTypeException:
    return None

if lookup:
    mti = lookup[0]
    try:
        context.restrictedTraverse(mti.icon_path)
        return mti.icon_path
    except (NotFound, KeyError, AttributeError): # Looking for 'NotFound' or KeyError
        pass

return context.getIcon()
