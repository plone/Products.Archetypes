from zope.interface import Interface

class IBaseObject(Interface):
    """ The most basic Archetypes-based implementation
    """

    def getId():
        """Get the object id
        """

    def setId(value):
        """Set the object id
        """

    def Type():
        """Dublin Core element - Object type

        this method is redefined in ExtensibleMetadata but we need this
        at the object level (i.e. with or without metadata) to interact
        with the uid catalog
        """

    def getField(key, wrapped=False):
        """Get a field by id
        """

    def getWrappedField(key):
        """Get a field by id which is explicitly wrapped
        """

    def getDefault(field):
        """Get default value for a field by id
        """

    def isBinary(key):
        """Check if an element is binary
        """

    def isTransformable(name):
        """Returns wether a field is transformable
        """

    def widget(field_name, mode="view", field=None, **kwargs):
        """Returns the rendered widget
        """

    def getContentType(key):
        """Content type for a field by key
        """

    def setContentType(value):
        """Sets the content type of the primary field
        """

    def getPrimaryField():
        """The primary field is some object that responds to
        PUT/manage_FTPget events.
        """

    def get_portal_metadata(field):
        """Returns the portal_metadata for a field
        """

    def Vocabulary(key):
        """Vocabulary for a field by key
        """

    def setDefaults():
        """Set default values for the fields
        """

    def update(**kwargs):
        """Update all fields and reindexObject
        """

    def edit(**kwargs):
        """Alias for update(**kwargs*)
        """

    def validate_field(name, value, errors):
        """Write a method: validate_foo(new_value) -> "error" or None

        If there is a validate method defined for a given field invoke it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """

    def pre_validate(REQUEST, errors):
        """Pre-validation hook
        """

    def post_validate(REQUEST, errors):
        """Post-validation hook
        """

    def validate(REQUEST, errors):
        """Validate fields
        """

    def SearchableText():
        """Full indexable text
        """

    def getCharset():
        """ Return site default charset, or utf-8
        """

    def get_size():
        """Used for FTP and apparently the ZMI now too
        """

    def processForm(data=1, metadata=0, REQUEST=None, values=None):
        """Process the schema looking for data in the form
        """

    def Schemata():
        """Returns the Schemata for the Object
        """

    def Schema():
        """Returns the full schema for the object.  NOTE: This method is
        usually added dynamically by ClassGen.
        """

    def addSubObjects(objects, REQUEST=None):
        """Add a dictionary of objects to the session
        """

    def getSubObject(name, REQUEST, RESPONSE=None):
        """Get a dictionary of objects from the session
        """

class IBaseContent(IBaseObject):
    """Contentish base interface marker

    BaseContent is subclassing the following classes, too:

    Products.Archetypes.Referenceable.Referenceable
    Products.Archetypes.CatalogMultiplex.CatalogMultiplex
    Products.CMFCore.PortalContent.PortalContent
    OFS.History.Historicall
    """


class IBaseFolder(IBaseObject):
    """Folderish base interface marker

    BaseFolder is subclassing the following classes, too:

    Products.CMFDefault.SkinnedFolder.SkinnedFolder
    OFS.Folder.Folder
    """

    def listFolderContents(contentFilter=None, suppressHiddenFiles=0):
        """
        Optionally you can suppress 'hidden' files, or files that begin with '.'
        """

    def folderlistingFolderContents(contentFilter=None, suppressHiddenFiles=0 ):
        """
        Calls listFolderContents in protected only by ACI so that folder_listing
        can work without the List folder contents permission, as in CMFDefault
        """

class IBaseUnit(Interface):
    """
    """

    def update(data, instance, **kw):
        """
        """

    def transform(instance, mt):
        """Takes a mimetype so object.foo.transform('text/plain') should return
        a plain text version of the raw content

        return None if no data or if data is untranformable to desired output
        mime type
        """

    def isBinary():
        """return true if this contains a binary value, else false"""

    def get_size():
        """
        """

    def getRaw(encoding=None, instance=None):
        """Return encoded raw value
        """

    def portalEncoding(instance):
        """Return the default portal encoding, using an external python script
        (look the archetypes skin directory for the default implementation)
        """

    def getContentType():
        """Return the imimetype object for this BU
        """

    def setContentType(instance, value):
        """
        """

    def content_type():
        """
        """

    def getFilename():
        """
        """

    def setFilename(filename):
        """
        """

    def index_html(REQUEST, RESPONSE):
        """download method
        """
