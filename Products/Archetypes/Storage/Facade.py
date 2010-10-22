from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Storage import StorageLayer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.Field import encode

from AccessControl import ClassSecurityInfo
from Products.Archetypes.Registry import registerStorage

class FacadeMetadataStorage(StorageLayer):
    """A Facade Storage which delegates to
    CMFMetadata's Metadata Tool for actually
    storing the metadata values
    """

    security = ClassSecurityInfo()

    def __init__(self, metadata_set):
        self.metadata_set = metadata_set

    security.declarePrivate('getTool')
    def getTool(self, instance):
        return getToolByName(instance, 'portal_metadata')

    security.declarePrivate('initializeInstance')
    def initializeInstance(self, instance, item=None, container=None):
        pass

    security.declarePrivate('initializeField')
    def initializeField(self, instance, field):
        pass

    security.declarePrivate('get')
    def get(self, name, instance, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        value = mdata[self.metadata_set][field.metadata_name]
        return value

    security.declarePrivate('set')
    def set(self, name, instance, value, **kwargs):
        field = kwargs['field']
        tool = self.getTool(instance)
        mdata = tool.getMetadata(instance)
        if isinstance(value, unicode):
            value = encode(value, instance)
        data = {field.metadata_name:value}
        # Calling _setData directly, because there's
        # *no* method for setting one field at a time,
        # and setValues takes a dict and does
        # validation, which prevents us from setting
        # values.
        mdata._setData(data, set_id=self.metadata_set)

    security.declarePrivate('unset')
    def unset(self, name, instance, **kwargs):
        pass

    security.declarePrivate('cleanupField')
    def cleanupField(self, instance, field, **kwargs):
        pass

    security.declarePrivate('cleanupInstance')
    def cleanupInstance(self, instance, item=None, container=None):
        pass

registerStorage(FacadeMetadataStorage)
