## Script (Python) "go_back"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##
from zLOG import LOG, INFO
REQUEST = context.REQUEST

portal = context.portal_url.getPortalObject()

LOG('lastest_referer', INFO, REQUEST.get('lastest_referer', 'NADA'))
portal_status_message='Add New Item Operation was Cancelled.'
referer = REQUEST.get('lastest_referer').pop()
return state.set(next_action='redirect_to:string:'+referer,
                 portal_status_message=portal_status_message)
