## Script (Python) "go_back"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=referrer
##title=Go Back
##
SESSION = context.REQUEST.SESSION
old_id = context.getId()
cflag = SESSION.get('__creation_flag__', {})

if old_id in cflag.keys():
    context.remove_creation_mark()
    context.aq_parent.manage_delObjects([old_id])
    portal_status_message=context.translate(
        msgid='message_edit_item_cancelled',
        domain='archetypes',
        default='Add new item operation was cancelled, object was removed.')
elif hasattr(context, 'isTemporary'):
    portal_status_message=context.translate(
        msgid='message_add_new_item_cancelled',
        domain='archetypes',
        default='Add New Item operation was cancelled.')
else:
    portal_status_message=context.translate(
        msgid='message_edit_item_cancelled',
        domain='archetypes',
        default='Item edition was cancelled.')

kwargs = {
    'next_action':'redirect_to:string:%s' % referrer,
    'portal_status_message':portal_status_message,
    }

env = state.kwargs
reference_source_url = env.get('reference_source_url')
if reference_source_url is not None:
    reference_source_url = env['reference_source_url'].pop()
    reference_source_field = env['reference_source_field'].pop()
    reference_source_fieldset = env['reference_source_fieldset'].pop()
    kwargs.update({
        'fieldset':reference_source_fieldset,
        'field':reference_source_field,
        'reference_focus':reference_source_field,
        })

return state.set(**kwargs)
