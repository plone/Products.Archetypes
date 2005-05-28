## Script (Python) "getCharset"
##title=Return the site charset
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

encoding = 'utf-8'
p_props = getattr(container, 'portal_properties', None)
if p_props is not None:
    site_props = getattr(p_props, 'site_properties', None)
    if site_props is not None:
        encoding = site_props.getProperty('default_charset')
return encoding
