## Script (Python) "setI18NCookie"
##title=
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=lang, cookie=1

REQUEST = context.REQUEST
if cookie:
    REQUEST.RESPONSE.setCookie('I18N_CONTENT_LANGUAGE',lang, path='/')
elif REQUEST.cookies.get('I18N_CONTENT_LANGUAGE',None):
    REQUEST.RESPONSE.expireCookie('I18N_CONTENT_LANGUAGE', path='/')


REQUEST.RESPONSE.redirect(REQUEST.environ['HTTP_REFERER'])

