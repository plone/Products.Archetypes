from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Storage import StorageLayer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.Field import encode, decode

class FacadeMetadataStorage(StorageLayer):
    """A Facade Storage which delegates to
    CMFMetadata's Metadata Tool for actually
    storing the metadata values
    """

    def __init__(self, metadata_set):
        self.metadata_set = metadata_set

    __implements__ = (IStorage, ILayer)

    def getTool(self, instance):
        return getToolByName(instance, 'portal_metadata')

    def initializeInstance(self, instance, item=None, container=None):
        pass

    def initializeField(self, instance, field):
        pass

    def get(self, name, instance, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        value = mdata[self.metadata_set][field.metadata_name]
        return value

    def set(self, name, instance, value, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        if type(value) == type(u''):
            value = encode(value, instance)
        data = {field.metadata_name:value}
        # Calling _setData directly, because there's
        # *no* method for setting one field at a time,
        # and setValues takes a dict and does
        # validation, which prevents us from setting
        # values.
        mdata._setData(data, set_id=self.metadata_set)

    def unset(self, name, instance, **kwargs):
        pass

    def cleanupField(self, instance, field, **kwargs):
        pass

    def cleanupInstance(self, instance, item=None, container=None):
        pass
