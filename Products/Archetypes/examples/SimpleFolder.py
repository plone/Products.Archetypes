from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema

class SimpleFolder(BaseFolder):
    """A simple folderish archetype"""
    schema = schema
    
    def manage_afterMKCOL(self, id, result, REQUEST=None, RESPONSE=None):
        """For unit tests
        """
        self.called_afterMKCOL_hook = True

registerType(SimpleFolder, PKG_NAME)
