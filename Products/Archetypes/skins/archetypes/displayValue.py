## Script (Python) "Display Value"
##title=Use DisplayList getValue method to translate internal value to a label
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=vocab, value, widget=None

t = context.restrictedTraverse('@@at_utils').translate
return t(vocab, value, widget)

