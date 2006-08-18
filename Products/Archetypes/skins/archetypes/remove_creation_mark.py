## Script (Python) "remove_creation_mark"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=id=None
##title=Clear __creation_flag__
##

# XXX This script doesn't seem to be used anymore.

from Products.CMFCore.utils import getToolByName

# Avoid implicitly creating a session if one doesn't exists
session = None
sdm = getToolByName(context, 'session_data_manager', None)

if sdm is not None:
    session = sdm.getSessionData(create=0)

if session is None:
    return

id = id and id or context.getId()

cflag = session.get('__creation_flag__', {})

if cflag.has_key(id):
    del cflag[id]

if session.has_key(id):
    del session[id]

session.set('__creation_flag__', cflag)
