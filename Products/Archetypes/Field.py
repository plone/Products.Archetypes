from __future__ import nested_scopes
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from types import ListType, TupleType, ClassType, FileType
from UserDict import UserDict
from Products.CMFCore  import CMFCorePermissions
from Globals import InitializeClass
from Widget import StringWidget, LinesWidget, \
     BooleanWidget, CalendarWidget, ImageWidget
from utils import capitalize, DisplayList
from debug import log, log_exc
from ZPublisher.HTTPRequest import FileUpload
from BaseUnit import BaseUnit
from types import StringType
from Storage import AttributeStorage, MetadataStorage
from DateTime import DateTime
from Layer import DefaultLayerContainer
from interfaces.field import IField, IObjectField
from interfaces.layer import ILayerContainer, ILayerRuntime, ILayer
from interfaces.storage import IStorage
from interfaces.base import IBaseUnit
from exceptions import ObjectFieldException
from Products.validation import validation


#For Backcompat and re-export
from Schema import FieldList, MetadataFieldList


class Field(DefaultLayerContainer):
    __implements__ = (IField, ILayerContainer)
    
    security  = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'required' : 0,
        'default' : None,
        'vocabulary' : (),
        'enforceVocabulary' : 0,
        'multiValued' : 0,
        'searchable' : 0,
        'isMetadata' : 0,

        'accessor' : None,
        'mutator' : None,
        'mode' : 'rw',

        'read_permission' : CMFCorePermissions.View,
        'write_permission' : CMFCorePermissions.ModifyPortalContent,

        'storage' : AttributeStorage(),
        'form_info' : None,

        'generateMode' : 'veVc',
        'force' : '',
        'type' : None,
        'widget': StringWidget,
        'validators' : (),
        'index' : None, # "KeywordIndex" "<type>|schema"
        }

    def __init__(self, name, **kwargs):
        DefaultLayerContainer.__init__(self)
        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)
        self.name = name

        self._widgetLayer()
        self._validationLayer()
        
        self.registerLayer('storage', self.storage)

    
    def __repr__(self):
        return "<Field %s(%s:%s)>" %(self.name, self.type, self.mode)

    def _widgetLayer(self):
        if hasattr(self, 'widget') and type(self.widget) == ClassType:
            self.widget = self.widget()

    def _validationLayer(self):
        # resolve that each validator is in the service
        # we could replace strings with class refs and keep
        # things impl the ivalidator in the list
        # XXX this is not compat with aq_ things like scripts with
        # __call__
        if type(self.validators) not in [type(()), type([])]:
            self.validators = (self.validators,)
            
        for v in self.validators:
            if not validation.validatorFor(v):
                log("WARNING: no validator %s for %s" % (v,
                self.name))

    def validate(self, value):
        for v in self.validators:
            res = validation.validate(v, value)
            if res != 1:
                return res
            return None

    def Vocabulary(self, content_instance=None):
        value = self.vocabulary
        if not isinstance(value, DisplayList):
            if content_instance and type(value) is StringType:
                method = getattr(content_instance, self.vocabulary, None)
                if method and callable(method):
                    value = method()
                    
            # Post process value into a DisplayList, templates will use
            # this interface
            sample = value[:1]
            if isinstance(sample, DisplayList):
                #Do nothing, the bomb is already set up
                pass
            elif type(sample) == type(()):
                #Assume we have ( (value, display), ...)
                #and if not ('', '', '', ...)
                if len(sample) != 2:
                    value = zip(value, value)
                value = DisplayList(value)
            elif len(sample) and type(sample[0]) == type(''):
                value = DisplayList(zip(value, value))
            else:
                log("Unhandled type in Vocab")
                log(value)

        return value 


class ObjectField(Field):
    """Base Class for Field objects that fundamentaly deal with raw
    data. This layer implements the interface to IStorage and other
    Field Types should subclass this to delegate through the storage
    layer. 
    """
    __implements__ = IObjectField
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'object',
        'default_content_type' : 'application/octet',
        })

    def get(self, instance, **kwargs):
        try:
            return self.storage.get(self.name, instance, **kwargs)
        except AttributeError: # happens if new Atts are added and not yet stored in the instance
            self.storage.set(self.name,instance,self.default,**kwargs)
            return self.default
        
    def set(self, instance, value, **kwargs):
        self.storage.set(self.name, instance, value, **kwargs)

    def unset(self, instance, **kwargs):
        self.storage.unset(self.name, instance, **kwargs)

    def setStorage(self, instance, storage):
        if not IStorage.isImplementedBy(storage):
            raise ObjectFieldException, "Not a valid Storage method"
        value = self.get(instance)
        self.unset(instance)
        self.storage = storage
        if hasattr(self.storage, 'initalizeInstance'):
            self.storage.initalizeInstance(instance)
        self.set(instance, value)

    def getStorage(self):
        return self.storage

StringField = ObjectField

class MetadataField(ObjectField):
    """Metadata fields have special storage and explictly no markup as
    requirements.
    """
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'metadata',
        'isMetadata' : 1,
        'generateMode' : 'mVc',
        'mode' : 'rw',
        'storage' : MetadataStorage(),
        })


class TextField(ObjectField):
    """Base Class for Field objects that rely on some type of
    transformation"""
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'text',
        'default' : '',
        'default_content_type' : 'text/plain',
        'default_output_type'  : 'text/plain',
        'allowable_content_types' : ('text/plain',),
        'primary' : 0,
        })
                       
    def defaultView(self):
        return self.default_output_type
    
    def set(self, instance, value, **kwargs):
        # We also need to handle the case where there is a baseUnit
        # for this field containing a valid set of data that would
        # not be reuploaded in a subsequent edit, this is basically
        # migrated from the old BaseObject.set method
        if not IBaseUnit.isImplementedBy(value):
            if value == '' or type(value) != StringType:
                unit = None
                try:
                    unit = ObjectField.get(self, instance)
                except AttributeError:
                    pass
                if unit and hasattr(aq_base(unit), 'filename') \
                   and getattr(unit, 'filename') != '':
                    if ((isinstance(value, FileUpload) and value.filename != '') or
                        (isinstance(value, FileType) and value.name != '')):
                        #OK, its a file, is it empty?
                        value.seek(-1, 2)
                        size = value.tell()
                        value.seek(0)
                        if size == 0:
                            # This new file has no length, so we keep
                            # the orig
                            return
                    elif value == '':
                        return #Empty strings don't overwrite either

            mime_type = kwargs.get('mime_type', 'text/plain')
            bu = BaseUnit(self.name, value, mime_type)
            #XXX bu = BaseUnit(self.name, instance, value, mime_type)
        else:
            bu = value
        ObjectField.set(self, instance, bu, **kwargs)

        #Invoke the default Transforms, hey, its policy
        #Note that we stash the product of transforms on
        #bu.transforms and BU deals with that
        #tt = getToolByName(self, "transformation_tool")
        #tt.runChains(MUTATION,
        #             bu.getRaw(),
        #             bu.transforms)
        

class DateTimeField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'datetime',
        'widget' : CalendarWidget,
        })

    def set(self, instance, value, **kwargs):
        if not isinstance(value, DateTime):
            try:
                value = DateTime(value)
            except:
                value = None
            
        ObjectField.set(self, instance, value, **kwargs)
        
class LinesField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'lines',
        'default' : [],
        'widget' : LinesWidget,
        })

    def set(self, instance, value, **kwargs):
        if type(value) == type(''):
            value =  value.split('\n')
        value = [v.strip() for v in value if v.strip()]
        value = filter(None, value)
        ObjectField.set(self, instance, value, **kwargs)

class IntegerField(ObjectField):
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'integer'
        })

    def set(self, instance, value, **kwargs):
        try:
            value = int(value)
        except TypeError:
            value = None
        
        ObjectField.set(self, instance, value, **kwargs)

class BooleanField(ObjectField):
    __implements__ = ObjectField.__implements__
    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'boolean',
        'default': None,
        'widget' : BooleanWidget,
        })

    def set(self, instance, value, **kwargs):
        
        if not value or value == '0':
            value = None ## False
        else:
            value = 1
        
        ObjectField.set(self, instance, value, **kwargs)
            


# ImageField.py 
# Written in 2003 by Christian Scholz (cs@comlounge.net)
# version: 1.0 (26/02/2002)
from OFS.Image import Image as BaseImage
from cStringIO import StringIO
try:
    import PIL.Image
    has_pil=1
except:
    # no PIL, no scaled versions!
    has_pil=None

class Image(BaseImage):
    def isBinary(self):
        log("isBin")
        return 1
    

class ImageField(ObjectField):
    """ implements an image attribute. it stores
        it's data in an image sub-object 

        sizes is an dictionary containing the sizes to
        scale the image to. PIL is required for that.

        Format:
        sizes={'mini': (50,50),
               'normal' : (100,100), ... }
        syntax: {'name': (width,height), ... }

        the scaled versions can then be accessed as
        object/<imagename>_<scalename>

        e.g. object/image_mini

        where <imagename> is the fieldname and <scalename>
        is the name from the dictionary

        original_size -- this parameter gives the size in (w,h)
        to which the original image will be scaled. If it's None,
        then no scaling will take place.
        This is important if you don't want to store megabytes of
        imagedata if you only need a max. of 100x100 ;-)

        example:

        ImageField('image',
            original_size=(600,600),
            sizes={ 'mini' : (80,80),
                    'normal' : (200,200),
                    'big' : (300,300),
                    'maxi' : (500,500)})
        
        will create an attribute called "image"
        with the sizes mini, normal, big, maxi as given
        and a original sized image of max 600x600.
        This will be accessible as
        object/image

        and the sizes as

        object/image_mini
        object/image_normal
        object/image_big
        object/image_maxi

        Scaling will only be available if PIL is installed!

        If 'DELETE_IMAGE' will be given as value, then all the images
        will be deleted (None is understood as no-op)
        """

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'original_size': (600,600),
        'sizes' : {'thumb':(80,80)},
        'default_content_type' : 'image/gif',
        'allowable_content_types' : ('image/gif','image/jpeg'),
        'widget': ImageWidget,
        })
                       
    default_view = "view"

    def defaultView(self):
        return self.form_info.defaultView() or self.default_view
    
    def set(self, instance, value, **kwargs):
        # do we have to delete the image?
        if value=="DELETE_IMAGE":
            ObjectField.set(self, instance, None, **kwargs)
            return

        if value == '' or type(value) != StringType:
            image = None
            try:
                image = ObjectField.get(self, instance)
            except AttributeError:
                pass

            # just keep stuff if nothing was uploaded
            if not value: return

            # check for file
            if not ((isinstance(value, FileUpload) and value.filename != '') or
                    (isinstance(value, FileType) and value.name != '')):
                return
                
            if image:
                #OK, its a file, is it empty?
                value.seek(-1, 2)
                size = value.tell()
                value.seek(0)
                if size == 0:
                 # This new file has no length, so we keep
                 # the orig
                 return

        ### 
        ### store the original
        ###

        # test for scaling it.
        if self.original_size and has_pil:
            mime_type = kwargs.get('mime_type', 'image/gif')
            image = Image(self.name, self.name, value, mime_type)
            data=image.data
            w,h=self.original_size
            imgdata=self.scale(data,w,h)
            mime_type="image/jpeg"
        else:
            mime_type = kwargs.get('mime_type', 'image/gif')
            imgdata=value

        image = Image(self.name, self.name, imgdata, mime_type)
        ObjectField.set(self, instance, image, **kwargs)


        # now create the scaled versions
        if not has_pil: 
            return

        data=image.data
        for n,size in self.sizes.items():
            w,h=size
            id=self.name+"_"+n
            imgdata=self.scale(data,w,h)
            image2=Image(id, self.name, imgdata, 'image/jpeg')
            # manually use storage
            self.storage.set(id,instance,image2)


    def scale(self,data,w,h):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        keys = {'height':int(w or h), 'width':int(h or w)} 

        original_file=StringIO(data)
        image=PIL.Image.open(original_file)
        image=image.convert('RGB')
        image.thumbnail((keys['width'],keys['height']))
        thumbnail_file=StringIO()
        image.save(thumbnail_file, "JPEG")
        thumbnail_file.seek(0)
        return thumbnail_file.read()



InitializeClass(Field)
