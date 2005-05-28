from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema

class SimpleBTreeFolder(BaseBTreeFolder):
    """A simple folderish archetype"""
    schema = schema
    
    def manage_afterMKCOL(self, id, result, REQUEST=None, RESPONSE=None):
        """For unit tests
        """
        self.called_afterMKCOL_hook = True

registerType(SimpleBTreeFolder, PKG_NAME)
