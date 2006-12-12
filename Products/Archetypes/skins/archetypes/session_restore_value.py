## Script (Python) "session_save_form"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fieldName,default
##title=Return field value previously stored on session by session_save_form
##

from Products.CMFCore.utils import getToolByName

# Avoid implicitly creating a session if one doesn't exists
session = None
sdm = getToolByName(context, 'session_data_manager', None)

if sdm is not None:
    session = sdm.getSessionData(create=0)

if session is None:
    return default

id = context.getId()
session_data = None

if session.has_key(id):
    session_dic = session.get(id)
    if session_dic.has_key(fieldName):
        session_data = session_dic.get(fieldName)

return session_data or default
