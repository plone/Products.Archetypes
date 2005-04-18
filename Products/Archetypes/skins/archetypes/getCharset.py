## Script (Python) "getCharset"
##title=Return the site charset
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
from Products.CMFCore.utils import getToolByName

utils = getToolByName(container, 'plone_utils', None)
if utils is not None:
    return utils.getSiteEncoding()
return 'utf-8'
