from Products.Archetypes.atapi import *
from Products.Archetypes.Marshall import PrimaryFieldMarshaller
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema + Schema((
    FileField('body',
              required=1,
              primary=1,
              widget=FileWidget(),
              ),
    ),
      marshall=PrimaryFieldMarshaller())

class SimpleFile(BaseContent):
    """An File (test) type"""
    schema = schema
    archetype_name = "Simple File Type"

    def manage_afterPUT(self, data, marshall_data, file, context, mimetype,
                        filename, REQUEST, RESPONSE):
        """For unit tests
        """
        self.called_afterPUT_hook = True

registerType(SimpleFile, PKG_NAME)
