## Script (Python) "add_reference"
##title=Add a new reference
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id='', add_reference=None
##
REQUEST = context.REQUEST

portal_status_message = REQUEST.get('portal_status_message',
                                    'New Reference Created.')

req_get = REQUEST.get

env = state.kwargs
for k in REQUEST.keys():
    if k.startswith('persistent_'):
        env.setdefault(k,REQUEST[k])

if (not state.kwargs.get('reference_source_url') and
    req_get('reference_source_url')):
    for name in ['reference_source_field',
                 'reference_source_url',
                 'reference_source_fieldset']:
        if env.has_key(name) and req_get(name):
            env[name].append(req_get(name))
        else:
            env[name] = req_get(name)
    return state.set(
        status='success',
        context=context,
        portal_status_message=portal_status_message)

context.session_save_form()

fieldset = REQUEST.get('fieldset', 'default')

field = context.Schemata()[fieldset][add_reference['field']]

destination = add_reference.destination

# get the portal object
portal = context.portal_url.getPortalObject()

# reference the destination context
destination = filter(None, destination.split('/'))
destination_context = portal.restrictedTraverse(destination)

# create a new object at destination context
new_id = destination_context.generateUniqueId(add_reference.type)
if context.portal_factory.getFactoryTypes().has_key(add_reference.type):
    destination_list = destination + \
        ['portal_factory', add_reference.type, new_id]
    reference_object = portal.restrictedTraverse(destination_list)
else:
    destination_context.invokeFactory(add_reference.type, new_id)
    reference_object = getattr(destination_context, new_id)
    reference_object.markCreationFlag()

info = {'reference_source_field':add_reference['field'],
        'reference_source_url':portal.portal_url.getRelativeUrl(context),
        'reference_source_fieldset':fieldset}

for k, v in info.items():
    if env.has_key(k):
        env[k].append(v)
    else:
        env[k] = [v]

return state.set(
    status='created',
    context=reference_object,
    portal_status_message=portal_status_message)
