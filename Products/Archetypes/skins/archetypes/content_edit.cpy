## Script (Python) "content_edit"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id=''
##
REQUEST = context.REQUEST

new_context = context.portal_factory.doCreate(context, id)
new_context.processForm()

portal_status_message = REQUEST.get('portal_status_message', 'Content changes saved.')

# handle navigation for multi-page edit forms
next = not REQUEST.get('form_next',None) is None
previous = not REQUEST.get('form_previous',None) is None

fieldset = REQUEST.get('fieldset', None)
schemata = new_context.Schemata()

if next or previous:
    s_names = [s for s in schemata.keys() if s != 'metadata']

    if previous:
        s_names.reverse()

    next_schemata = None
    try:
        index = s_names.index(fieldset)
    except ValueError:
        raise 'Non-existing fieldset: %s' % fieldset
    else:
        index += 1
        if index < len(s_names):
            next_schemata = s_names[index]
            return state.set(status='next_schemata',
                             context=new_context,
                             fieldset=next_schemata,
                             portal_status_message=portal_status_message)

    if next_schemata == None:
        raise 'Unable to find next field set after %s' % fieldset

env = state.kwargs
reference_source_url = env.get('reference_source_url')
if reference_source_url is not None:
    reference_source_url = env['reference_source_url'].pop()
    reference_source_field = env['reference_source_field'].pop()
    reference_source_fieldset = env['reference_source_fieldset'].pop()
    portal = context.portal_url.getPortalObject()
    new_context = portal.restrictedTraverse(reference_source_url)
    return state.set(status='success_add_reference',
                     context=new_context,
                     portal_status_message='Reference Added.',
                     fieldset=reference_source_fieldset,
                     field=reference_source_field)

if state.errors:
    errors = state.errors
    s_items = [(s, schemata[s].keys()) for s in schemata.keys()]
    fields = []
    for s, f_names in s_items:
        for f_name in f_names:
            fields.append((s, f_name))
    for s_name, f_name in fields:
        if errors.has_key(f_name):
            REQUEST.set('fieldset', s_name)
            return state.set(
                status='failure',
                context=new_context,
                portal_status_message=portal_status_message)

return state.set(status='success',
                 context=new_context,
                 portal_status_message=portal_status_message)
