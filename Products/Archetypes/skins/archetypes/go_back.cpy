## Script (Python) "go_back"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=lastest_referer
##title=Go Back
##
portal_status_message=context.translate(
    msgid='message_add_new_item_cancelled',
    domain='archetypes',
    default='Add New Item operation was cancelled.')

return state.set(next_action='redirect_to:string:%s' % lastest_referer,
                 portal_status_message=portal_status_message)
