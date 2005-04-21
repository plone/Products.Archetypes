from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema

class SimpleFolder(BaseFolder):
    """A simple folderish archetype"""
    schema = schema

registerType(SimpleFolder, PKG_NAME)
