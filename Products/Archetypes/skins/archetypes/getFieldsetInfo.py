##parameters=errors={},schematas=[],fieldsets=[]

"""
this script tries to collect all information needed
to display fieldsets properly. This is:


- the default fieldset to show
- the fieldsets which do have errors

"""

# mark all fieldsets with errors as key so we emulate a set
fieldsets_with_errors={}

# get the error fields
error_ids = errors.keys()

# if there are no errors, then just show first fieldset
if not len(error_ids):
    return {'default'               : 'default',
            'fieldsets_with_errors' : []}

# now search for that field in all fieldsets
for fieldset in fieldsets:
    fields = schematas[fieldset].editableFields(context)
    field_ids = [field.getName() for field in fields]
    for eid in error_ids:
        if eid in field_ids:
            fieldsets_with_errors[fieldset]=1

fs = fieldsets_with_errors.keys()
if len(fs)==0:
    return {'default'               : 'default',
            'fieldsets_with_errors' : []}
else:
    # if there are errors, then show the first fieldset with one
    return {'default'               : fs[0],
            'fieldsets_with_errors' : fs}


