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

fieldset = REQUEST.get('fieldset', 'default')

field = context.Schemata()[fieldset][add_reference['field']]
destination = field.widget.getDestination(context)
mutator = field.getMutator(context)
accessor = field.getAccessor(context)

# get the portal object
portal = context.portal_url.getPortalObject()

# reference the destination context
destination = filter(None, destination.split('/'))
destination_context = portal.restrictedTraverse(destination)

# create a new object at destination context
new_id = destination_context.generateUniqueId(add_reference.type)
destination_context.invokeFactory(add_reference.type, new_id)
reference_object = getattr(destination_context, new_id)

ref = reference_object.UID()

# If the field is multiValued, we must pass the existing
# references in addition to the new one.
if field.multiValued:
    existing = tuple(accessor())
    ref = (ref,)
    ref = existing and ref + existing or ref

# set a reference to the newly-created object
mutator(ref)

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
