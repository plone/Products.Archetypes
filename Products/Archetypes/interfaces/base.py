from Interface import Interface, Attribute

class IBaseObject(Interface):
    """ Base Object """

    #XXX windows is strange
    #schema = Attribute('schema', 'Schema of the object')
    #installMode = Attribute('installMode', 'Used for installation. List of actions to perform.')

    #typeDescription = Attribute('Type description used for base_edit')
    #typeDescMsgId = Attribute('I18N message id for type description')

    # CMFCorePermissions.ModifyPortalContent
    def initializeLayers(item=None, container=None):
        """ Layer initialization. Performed on __init__ """

    def getId():
        """get the objects id"""

    # CMFCorePermissions.ModifyPortalContent
    def setId(value):
        """set the object id"""

    def Type():
        """Dublin Core element - Object type

        this method is redefined in ExtensibleMetadata but we need this
        at the object level (i.e. with or without metadata) to interact
        with the uid catalog
        """

    # CMFCorePermissions.ModifyPortalContent
    def getField(key):
        """get a field by id"""

    def getDefault(field):
        """get default value for a field by id"""

    def isBinary(key):
        """check if an element is binary"""

    def isTransformable(name):
        """Returns wether a field is transformable
        """

    def widget(field_name, mode="view", field=None, **kwargs):
        """Returns the rendered widget
        """

    def getContentType(key):
        """content type for a field by key"""

    # CMFCorePermissions.ModifyPortalContent
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
        """vocabulary for a field by key"""

    # CMFCorePermissions.ModifyPortalContent
    def edit(**kwargs):
        """edit"""

    # CMFCorePermissions.ModifyPortalContent
    def setDefaults():
        """set default values for the fields. called on __init__"""

    # CMFCorePermissions.ModifyPortalContent
    def update(**kwargs):
        """update all fields and reindexObject"""

    # CMFCorePermissions.ModifyPortalContent
    def edit(**kwargs):
        """Alias for update(**kwargs*)
        """

    def validate_field(name, value, errors):
        """
        write a method: validate_foo(new_value) -> "error" or None
        If there is a validate method defined for a given field invoke it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """
        methodName = "validate_%s" % name

        base = aq_base()
        if hasattr(base, methodName):
            method = getattr(base, methodName)
            result = method(value)
            if result is not None:
                errors[name] = result


    def pre_validate(REQUEST, errors):
        """pre-validation hook"""

    def post_validate(REQUEST, errors):
        """post-validation hook"""

    def validate(REQUEST, errors):
        """validate fields"""

    def SearchableText():
        """full indexable text"""

    def getCharset():
        """ Return site default charset, or utf-8
        """

    def get_size():
        """ Used for FTP and apparently the ZMI now too """

    def processForm(data=1, metadata=0, REQUEST=None, values=None):
        """Process the schema looking for data in the form"""

    def Schemata():
        """Returns the Schemata for the Object
        """

    def addSubObjects(objects, REQUEST=None):
        """add a dictionary of objects to the session
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

    def listFolderContents(spec=None, contentFilter=None, suppressHiddenFiles=0):
        """
        Optionally you can suppress "hidden" files, or files that begin with .
        """

    def folderlistingFolderContents(spec=None, contentFilter=None,
                                    suppressHiddenFiles=0 ):
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
        """return encoded raw value
        """

    def portalEncoding(instance):
        """return the default portal encoding, using an external python script
        (look the archetypes skin directory for the default implementation)
        """

    def getContentType():
        """return the imimetype object for this BU
        """

    def setContentType(value):
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
