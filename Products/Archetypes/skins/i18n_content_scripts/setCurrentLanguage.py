## Script (Python) "setCurrentLanguage"
##title=set the current content language
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=lang, old_lang=None, sync_translation_service=0, cookie=0, referer=1, redirect=1

REQUEST = context.REQUEST

# check this is a valid language id
container.languageDescription(lang)

# store current language in a session variable
REQUEST.SESSION['CONTENT_LANGUAGE'] = lang

# store old language in a session variable if any
if old_lang is not None:
    REQUEST.SESSION['PREV_CONTENT_LANGUAGE'] = old_lang
else:
    try:
        del REQUEST.SESSION['PREV_CONTENT_LANGUAGE']
    except:
        pass

# optionaly save selected language in a cookie for next session
if cookie:
    REQUEST.RESPONSE.setCookie('CONTENT_LANGUAGE', lang, path='/')
#elif REQUEST.cookies.get('CONTENT_LANGUAGE',None):
#    REQUEST.RESPONSE.expireCookie('CONTENT_LANGUAGE', path='/')


# FIXME : sync_translation_service

if redirect:
    try:
        context.needLanguageRedirection()
    except:
        pass
    if referer:
        REQUEST.RESPONSE.redirect(REQUEST.environ['HTTP_REFERER'])
    else:
        REQUEST.RESPONSE.redirect(REQUEST.URL)
