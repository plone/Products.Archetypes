from Products.Archetypes.atapi import *

schema = BaseSchema

class SimpleBTreeFolder(BaseBTreeFolder):
    """A simple folderish archetype"""
    schema = schema

registerType(SimpleBTreeFolder)
