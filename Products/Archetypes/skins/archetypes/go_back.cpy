## Script (Python) "go_back"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=lastest_referer
##
REQUEST = context.REQUEST

portal = context.portal_url.getPortalObject()

portal_status_message='Add New Item Operation was Cancelled.'
return state.set(next_action='redirect_to:string:'+lastest_referer,
                 portal_status_message=portal_status_message)
