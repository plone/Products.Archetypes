## Script (Python) "getContentLanguage"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=return the id for the current content language (context sensitive)
##parameters=lang=None,check_context=1

if check_context:
    if not lang and hasattr(context, 'hasI18NContent') and context.hasI18NContent():
        lang = context.getCurrentLanguage()
elif not lang:
    lang = context.getCurrentLanguage()
    
if not lang and hasattr(context, 'Language'):
    lang = context.Language()
    
if not lang:
    try:
        sp = context.portal_properties.site_properties
        lang = sp.getProperty('default_language', 'en')
    except AttributeError:
        lang = None

return lang or "en"
