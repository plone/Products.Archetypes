REQUEST = context.REQUEST
# hey, don't forget to increment object number for sessions
form_data = {'HTTP_REFERER':REQUEST.get('lastest_referer', None)}
to_store = [f for f in context.schema.values() if f.type != 'computed']
for field in to_store:
    fieldname = field.getName()
    # is there other way to know if field is KeywordWidget here?
    # this is so ugly :~/
    if field.widget.macro == 'widgets/keyword':
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
REQUEST.SESSION.set(context.getId(), form_data)
