## Script (Python) "getContentLanguage"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=return the id for the current content language (context sensitive)
##parameters=lang=None
if lang:
    return lang

if hasattr(context, 'hasI18NContent') and context.hasI18NContent():
    return context.getCurrentLanguage()
    
if hasattr(context, 'Language'):
    lang = context.Language()
    
if not lang:
    try:
        sp = context.portal_properties.site_properties
        lang = sp.getProperty('default_language', 'en')
    except AttributeError:
        lang = None

return lang or "en"
