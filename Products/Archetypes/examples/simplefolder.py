from Products.Archetypes.atapi import *

schema = BaseSchema

class SimpleFolder(BaseFolder):
    """A simple folderish archetype"""
    schema = schema

registerType(SimpleFolder)
