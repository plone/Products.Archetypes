## Script (Python) "change_lang"
##title=update language is if has been changed by the edit view
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath

REQUEST = context.REQUEST

if context.hasI18NContent():
   oldLang = REQUEST.SESSION.get('PREV_CONTENT_LANGUAGE', None)
   if oldLang is not None:
      context.setCurrentLanguage(lang=oldLang)
      del REQUEST.SESSION['PREV_CONTENT_LANGUAGE']
      
portal_status_message = REQUEST.get('portal_status_message', 'Content changes saved.')
return ('success', context, {'portal_status_message':portal_status_message})
