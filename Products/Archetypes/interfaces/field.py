from interface import Interface, Attribute

class IField(Interface):
    """ Interface for fields """

#     required = Attribute('required', 'Require a value to be present when submitting the field')
#     default = Attribute('default', 'Default value for a field')
#     vocabulary = Attribute('vocabulary', 'List of suggested values for the field')
#     enforceVocabulary = Attribute('enforceVocabulary', \
#                                   'Restrict the allowed values to the ones in the vocabulary')
#     multiValued = Attribute('multiValued', 'Allow the field to have multiple values')
#     searchable = Attribute('searchable', 'Make the field searchable')
#     isMetadata = Attribute('isMetadata', 'Is this field a metadata field?')
#     accessor = Attribute('accessor', 'Use this method as the accessor for the field')
#     mutator = Attribute('mutator', 'Use this method as the mutator for the field')
#     mode = Attribute('mode', 'Mode of access to this field')
#     read_permission = Attribute('read_permission', \
#                                 'Permission to use to protect field reading')
#     write_permission = Attribute('write_permission', \
#                                  'Permission to use to protect writing to the field')

#     storage = Attribute('storage', 'Storage class to use for this field')
#     form_info = Attribute('form_info', 'Form Info (?)')
#     generateMode = Attribute('generateMode', 'Generate Mode (?)')
#     force = Attribute('force', 'Force (?)')
#     type = Attribute('type', 'Type of the field')

    def Vocabulary(content_instance):
        """ Vocabulary of allowed values for this field """

class IObjectField(IField):
    """ Interface for fields that support a storage layer """

    def get(instance, **kwargs):
        """ Get the value for this field using the underlying storage """

    def set(instance, value, **kwargs):
        """ Set the value for this field using the underlying storage """

    def unset(instance, **kwargs):
        """ Unset the value for this field using the underlying storage """

    def getStorage():
        """ Return the storage class used in this field """

    def setStorage(instance, storage):
        """ Set the storage for this field to the give storage.
        Values are migrated by doing a get before changing the storage
        and doing a set after changing the storage.

        The underlying storage must take care of cleaning up of removing
        references to the value stored using the unset method."""
