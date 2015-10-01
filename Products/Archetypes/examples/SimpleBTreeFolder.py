from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema


class SimpleBTreeFolder(BaseBTreeFolder):
    """A simple folderish archetype"""
    schema = schema

    def manage_afterMKCOL(self, id, result, REQUEST=None, RESPONSE=None):
        """For unit tests
        """
        self.called_afterMKCOL_hook = True

    def manage_afterPUT(self, data, marshall_data, file, context, mimetype,
                        filename, REQUEST, RESPONSE):
        """For unit tests
        """
        self.called_afterPUT_hook = True

registerType(SimpleBTreeFolder, PKG_NAME)
