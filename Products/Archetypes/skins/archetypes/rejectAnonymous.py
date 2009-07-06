## Script (Python) "rejectAnonymous"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.utils import addStatusMessage

if context.portal_membership.isAnonymousUser():

    url = '%s/login_form' % context.portal_url()
    addStatusMessage(REQUEST, _(u'You must sign in first.'), type='info')

    RESPONSE=context.REQUEST.RESPONSE
    return RESPONSE.redirect(url)
return True
