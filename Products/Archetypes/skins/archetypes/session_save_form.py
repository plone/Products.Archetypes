## Script (Python) "session_save_form"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Introspect context schema and saves on session REQUESTs values
##
REQUEST = context.REQUEST

# hey, don't forget to increment object number for sessions
form_data = {'HTTP_REFERER':REQUEST.get('last_referer', None)}
to_store = [f for f in context.Schema().values() if f.type != 'computed']

for field in to_store:
    fieldname = field.getName()
    if field.widget.getName() == 'KeywordWidget':
        fieldname = '%s_keywords' % field.getName()
        data = []
        if REQUEST.has_key(fieldname):
            data += REQUEST.get(fieldname)
        fieldname = '%s_existing_keywords' % field.getName()
        if REQUEST.has_key(fieldname):
            data += REQUEST.get(fieldname)
        form_data[field.getName()] = data
    else:
        if REQUEST.has_key(fieldname):
            form_data[fieldname] = REQUEST.get(fieldname)

# XXX Implicitly creating a session for user.
REQUEST.SESSION.set(context.getId(), form_data)
