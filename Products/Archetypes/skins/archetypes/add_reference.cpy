## Script (Python) "add_reference"
##title=Add a new reference
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id='', add_reference=None

REQUEST = context.REQUEST
portal_status_message = REQUEST.get('portal_status_message', 'New Reference Created.')

if not state.kwargs.get('original_url') and REQUEST.get('original_url'):
    return state.set(status='success',
                     context=context,
                     portal_status_message=portal_status_message,
                     original_field=REQUEST.get('original_field'),
                     original_url=REQUEST.get('original_url'),
                     original_fieldset=REQUEST.get('original_fieldset'))

fieldset = REQUEST.get('fieldset', 'default')

field = context.Schemata()[fieldset][add_reference.field]
destination = field.widget.destination
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

return state.set(status='created',
                 context=reference_object,
                 portal_status_message=portal_status_message,
                 original_field=add_reference.field,
                 original_url=portal.portal_url.getRelativeUrl(context),
                 original_fieldset=fieldset)
