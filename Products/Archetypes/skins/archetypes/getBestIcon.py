## Script (Python) "getBestIcon"
##title=Find most specific icon for an (sub)object
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
from Products.CMFCore.utils import getToolByName
mtr = getToolByName(context, 'mimetypes_registry', None)
if mtr is not None:
    mtiList = mtr.lookup(context.getContentType())
    if len(mtiList):
        return mtiList[0].icon_path
else:
    return context.getIcon()
