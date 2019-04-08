## Script (Python) "unicodeTestIn"
##title=Test if a unicode string is in a unicode list
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=value, vocab

if vocab is None or len(vocab) == 0:
    return 0
if not isinstance(value, str):
    value = value.encode('utf-8')
for v in vocab:
    if not isinstance(v, str):
        v = v.encode('utf-8')
    if v == value:
        return True
return False
