from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema

class SimpleBTreeFolder(BaseBTreeFolder):
    """A simple folderish archetype"""
    schema = schema

registerType(SimpleBTreeFolder, PKG_NAME)
