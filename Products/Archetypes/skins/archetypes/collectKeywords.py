## Script (Python) "collectKeywords"
##title=Edit content
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=name, index, vocab_source='portal_catalog'
REQUEST=context.REQUEST


## With the advent of multi-cataloging we need to pass an optional
## catalog id to use for the widget.

allowed, enforce = context.Vocabulary(name)
catalog = getattr(container, vocab_source)
previous = catalog.uniqueValuesFor(index)

if enforce:
    result = allowed
else:
    result = allowed + previous

result = result.sortedByValue()

return result
