## Script (Python) "session_save_form"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fieldName,default
##title=Return field value previously stored on session by session_save_form
##
id = context.getId()
SESSION = context.REQUEST.SESSION
session_data = None
if SESSION.has_key(id):
    session_dic = SESSION.get(id)
    if session_dic.has_key(fieldName):
        session_data = session_dic.get(fieldName)
return session_data or default
