## Script (Python) "getUniqueWidgetAttr"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fields, attr
##

order = []

for f in fields:
    widget = f.widget
    helper = getattr(widget, attr, None)
    # We expect the attribute value to be a iterable.
    if helper:
        # I love list comprehension ;)
        [order.append(item) for item in helper
         if item not in order]

return order
