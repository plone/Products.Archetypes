## Script (Python) "lookupMime"
##title=Given an id, return the human representation of mime-type.
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=name

mimetool = context.mimetypes_registry
mimetypes = mimetool.lookup(name)
if len(mimetypes):
    return mimetypes[0].name()
else:
    return name
