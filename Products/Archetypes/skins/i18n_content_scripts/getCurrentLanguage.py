## Script (Python) "getCurrentLanguage"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=return the id for the current language
##parameters=

REQUEST = context.REQUEST

# first check for the current language in the session variable
try:
    lang = REQUEST.SESSION['CONTENT_LANGUAGE']
except:
    # then in a cookie
    if hasattr(REQUEST, 'cookies'):
        lang = REQUEST.cookies.get('CONTENT_LANGUAGE', None)
        
    # else use default language from site properties
    if not lang:
        try:
            sp = context.portal_properties.site_properties
            lang = sp.getProperty('default_language', 'en')
        except AttributeError:
            lang = 'en'

return lang or "en"
