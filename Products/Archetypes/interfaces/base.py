from interface import Interface, Attribute

class IBaseObject(Interface):
    
    schema = Attribute('schema', 'Schema of the object')
    installMode = Attribute('installMode', 'Used for installation. List of actions to perform.')
    
    def initializeLayers(item=None, container=None):
        """ Layer initialization. Performed on __init__ """

    def getId():
        """get the objects id"""

    def setId(value):
        """set the object id"""

    def getField(key):
        """get a field by id"""

    def getDefault(field):
        """get default value for a field by id"""
    
    def isBinary(key):
        """check if an element is binary"""

    def getContentType(key):
        """content type for a field by key"""

    def Vocabulary(key):
        """vocabulary for a field by key"""

    def edit(**kwargs):
        """edit"""

    def setDefaults():
        """set default values for the fields. called on __init__"""
            
    def update(**kwargs):
        """update all fields and reindexObject"""

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
    
    def get_size():
        """ Used for FTP and apparently the ZMI now too """

class IBaseContent(IBaseObject):
    """Contentish base interface marker"""
    pass

class IBaseFolder(IBaseObject):
    """Folderish base interface marker"""
    pass

class IBaseUnit(Interface):
    pass
