## Script (Python) "getCharset"
##title=Return the site charset
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
from Products.CMFCore.utils import getToolByName

properties = getToolByName(container, 'portal_properties', None)
if properties is not None:
    site_properties = getattr(properties, 'site_properties', None)
    if site_properties is not None:
        return site_properties.getProperty('default_charset')

return 'utf-8'
