from AccessControl import Unauthorized
from Acquisition import Implicit
from OFS.SimpleItem import Item
from zope.interface import implements
from zope.traversing.interfaces import ITraversable

class FieldView(Item, Implicit):
    
    def __init__(self, context, request, field, storage):
        self.context = context
        self.request = request
        self.field = field
        self.storage = storage
    
    def __call__(self):   
        if not self.field.checkPermission('r', self.context):
            raise Unauthorized, \
                  'Your not allowed to access the requested field %s.' % \
                  self.field.getName()
        value = self.field.getStorage(self.context).get(self.storage, 
                                                        self.context)
        if hasattr(value, 'index_html'):
            # for file- and image object i.e. from OFS.Image
            return value.index_html(self.request, self.request.response)
        # TODO: check if theres some other special case 
        return value

class FieldTraverser(object):
    """Used to traverse to a Archetypes field and access its storage.
    
    useful together with AnnotationStorage if you dont want to hack __bobo__
    
    usage: in url this traverser can be used to access a fields data by use of
           the fieldname and the storage variant if needed (such as image sizes)
           
           in url its: obj/++atfield++FIELDNAME
           or:         obj/++atfield++FIELDNAME-STORAGENAME 
           
    example: to access an original site image from a field named 'photo':
             obj/++atfield++photo
             
             to access its thumbnail with size name thumb:
             obj/++atfield++photo-thumb
    """
    implements(ITraversable)
    
    def __init__(self, context, request=None):
        self.context = context
        self.request = request
        
    def traverse(self, name, ignore):
        if '-' in name:
            fieldname, storage = name.split('-')
            storage = '%s_%s' % (fieldname, storage)
        else:
            fieldname, storage = name, name
        field = self.context.Schema().get(fieldname, None)        
        if field is None:
            return None
        return FieldView(self.context, self.request, field, storage).__of__(self.context)
    