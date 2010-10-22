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

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.utils import addStatusMessage

REQUEST = context.REQUEST
message = _(u'New reference created.')
addStatusMessage(REQUEST, message, type='info')

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
        context=context)

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

# The following code checks the submitted form for an 'associate_ref' list
# value.  if the field exists, and the name of the ReferenceField is among the
# listed values, then the reference will be associated immediately upon
# creation. If not, then the reference will not become associated until the
# reference source object is saved (i.e. current behaviour remains).
if add_reference['field'] in req_get('associate_ref', []):
    if field.multiValued:
        field.getMutator(context)(field.getAccessor(context)() + [reference_object])
    else:
        field.getMutator(context)(reference_object)

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
    context=reference_object)
