## Script (Python) "Display Value"
##title=Use DisplayList getValue method to translate internal value to a label
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=vocab, value

try:
    return u', '.join([vocab.getValue(unicode(str(v))) for v in value])
except TypeError:
    return vocab.getValue(unicode(str(value)))

