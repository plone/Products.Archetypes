REQUEST = context.REQUEST
# hey, don't forget to increment object number for sessions
form_data = {'HTTP_REFERER':REQUEST.get('lastest_referer', None)}
to_store = [f for f in context.Schema().values() if f.type != 'computed']
for field in to_store:
    fieldname = field.getName()
    if REQUEST.has_key(fieldname):
        form_data[fieldname] = REQUEST.get(fieldname)
REQUEST.SESSION.set(context.getId(), form_data)
