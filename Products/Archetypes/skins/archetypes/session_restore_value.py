##parameters=fieldName,default
id = context.getId()
SESSION = context.REQUEST.SESSION
session_data = None
if SESSION.has_key(id):
    session_dic = SESSION.get(id)
    if session_dic.has_key(fieldName):
        session_data = session_dic.get(fieldName)
return session_data or default
