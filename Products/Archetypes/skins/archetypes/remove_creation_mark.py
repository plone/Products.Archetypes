##parameters=id=None
SESSION = context.REQUEST.SESSION
id = id and id or context.getId()
cflag = SESSION.get('__creation_flag__', {})
if cflag.has_key(id):
    del cflag[id]
if SESSION.has_key(id):
    del SESSION[id]
SESSION.set('__creation_flag__', cflag)
