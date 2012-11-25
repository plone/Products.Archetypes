## Script (Python) "getUniqueWidgetAttr"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=fields, attr
##title=Edit content
##
from Products.CMFCore.utils import getToolByName
ltool = getToolByName(context, 'portal_languages', None)
if ltool:
    preferred_language = ltool.getPreferredLanguage()
else:
    preferred_language = 'en'

order = []
for f in fields:
    widget = f.widget
    helper = getattr(widget, attr, None)

    # We expect the attribute value to be a iterable.
    if helper:
        for item in helper:
            if attr == 'helper_js' and preferred_language != 'en':
                if item.endswith('-en.js'):
                    item = item.replace('-en.js', 
                                        '-%s.js' % preferred_language)

            if item not in order:
                order.append(item)

return order
