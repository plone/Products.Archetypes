# common imports
from types import StringType
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storages import AttributeStorage
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.vocabulary import DisplayList
from basefields import Field
from basefields import ObjectField

# imports specific for this field
from types import DictType
from cgi import escape
from ExtensionClass import Base
from Acquisition import Implicit
from Globals import InitializeClass
from ZODB.POSException import ConflictError
from BTrees.OOBTree import OOBTree
from OFS.Image import Image as BaseImage
from OFS.Traversable import Traversable
from OFS.Cache import ChangeCacheSettingsPermission
from Products.Archetypes.config import HAS_PIL
from Products.Archetypes.widgets import ImageWidget
from Products.Archetypes.fields import FileField
from Products.Archetypes.fields.basefields import ObjectField
if HAS_PIL:
    import PIL


__docformat__ = 'reStructuredText'

# ImageField.py
# Written in 2003 by Christian Scholz (cs@comlounge.net)
# version: 1.0 (26/02/2002)

class Image(BaseImage):

    security  = ClassSecurityInfo()

    def title(self):
        parent = aq_parent(aq_inner(self))
        if parent is not None:
            return parent.Title() or parent.getId()
        return self.getId()

    title = ComputedAttribute(title, 1)

    alt = title_or_id = title

    def isBinary(self):
        return True

class ImageField(FileField):
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

        max_size -- similar to max_size but if it's given then the image
                    is checked to be no bigger than any of the given values
                    of width or height.
                    XXX: I think it is, because the one who added it did not
                    document it ;-) (mrtopf - 2003/07/20)

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

        sizes may be the name of a method in the instance or a callable which
        returns a dict.

        Scaling will only be available if PIL is installed!

        If 'DELETE_IMAGE' will be given as value, then all the images
        will be deleted (None is understood as no-op)
        """

    # XXX__implements__ = FileField.__implements__ , IImageField

    _properties = FileField._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'original_size': None,
        'max_size': None,
        'sizes' : {'thumb':(80,80)},
        'swallowResizeExceptions' : False,
        'default_content_type' : 'image/png',
        'allowable_content_types' : ('image/gif','image/jpeg','image/png'),
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        'content_class': Image,
        })

    security  = ClassSecurityInfo()

    default_view = "view"

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        if not value:
            return

        # Do we have to delete the image?
        if value=="DELETE_IMAGE":
            self.removeScales(instance, **kwargs)
            # unset main field too
            ObjectField.unset(self, instance, **kwargs)
            return

        if not kwargs.has_key('mimetype'):
            kwargs['mimetype'] = None

        value, mimetype, filename = self._process_input(value,
                                                      default=self.getDefault(instance),
                                                      **kwargs)
        #print type(value), mimetype, filename

        kwargs['mimetype'] = mimetype
        kwargs['filename'] = filename

        kwargs = self._updateKwargs(instance, value, **kwargs)
        try:
            imgdata = self.rescaleOriginal(value, **kwargs)
        except ConflictError:
            raise
        except:
            if not self.swallowResizeExceptions:
                raise
            else:
                imgdata = value
                log_exc()
        # XXX add self.ZCacheable_invalidate() later
        self.createOriginal(instance, imgdata, **kwargs)
        self.createScales(instance)

    def _updateKwargs(self, instance, value, **kwargs):
        # get filename from kwargs, then from the value
        # if no filename is available set it to ''
        vfilename = getattr(value, 'filename', '')
        kfilename = kwargs.get('filename', '')
        if kfilename:
            filename = kfilename
        else:
            filename = vfilename
        kwargs['filename'] = filename

        # set mimetype from kwargs, then from the field itself
        # if no mimetype is available set it to 'image/png'
        kmimetype = kwargs.get('mimetype', None)
        if kmimetype:
            mimetype = kmimetype
        else:
            try:
                mimetype = self.getContentType(instance)
            except RuntimeError:
                mimetype = None
        kwargs['mimetype'] = mimetype and mimetype or 'image/png'
        return kwargs

    security.declareProtected(CMFCorePermissions.View, 'getAvailableSizes')
    def getAvailableSizes(self, instance):
        """Get sizes

        Supports:
            self.sizes as dict
            A method in instance called like sizes that returns dict
            A callable
        """
        sizes = self.sizes
        if type(sizes) is DictType:
            return sizes
        elif type(sizes) is StringType:
            assert(shasattr(instance, sizes))
            method = getattr(instances, sizes)
            data = method()
            assert(type(data) is DictType)
            return data
        elif callable(sizes):
            return sizes()
        elif sizes is None:
            return {}
        else:
            raise TypeError, 'Wrong self.sizes has wrong type' % type(sizes)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'rescaleOriginal')
    def rescaleOriginal(self, value, **kwargs):
        """rescales the original image and sets the data

        for self.original_size or self.max_size
        """
        mimetype = kwargs.get('mimetype', 'image/png')
        if HAS_PIL:
            if self.original_size or self.max_size:
                image = self.content_class(self.getName(), self.getName(),
                                         value, mimetype)
                data = str(image.data)
                w=h=0
                if self.max_size:
                    if image.width > self.max_size[0] or \
                           image.height > self.max_size[1]:
                        factor = min(float(self.max_size[0])/float(image.width),
                                     float(self.max_size[1])/float(image.height))
                        w = int(factor*image.width)
                        h = int(factor*image.height)
                elif self.original_size:
                    w,h = self.original_size
                if w and h:
                    fvalue, format = self.scale(data,w,h)
                    value = fvalue.read()
        return value

    security.declarePrivate('createOriginal')
    def createOriginal(self, instance, value, **kwargs):
        """create the original image (save it)
        """
        image = self._wrapValue(instance, value, **kwargs)

        ObjectField.set(self, instance, image, **kwargs)

    security.declarePrivate('removeScales')
    def removeScales(self, instance, **kwargs):
        """Remove the scaled image
        """
        sizes = self.getAvailableSizes(instance)
        if sizes:
            for name, size in sizes.items():
                id = self.getName() + "_" + name
                try:
                    # the following line may throw exceptions on types, if the
                    # type-developer add sizes to a field in an existing
                    # instance and a user try to remove an image uploaded before
                    # that changed. The problem is, that the behavior for non
                    # existent keys isn't defined. I assume a keyerror will be
                    # thrown. Ignore that.
                    self.getStorage(instance).unset(id, instance, **kwargs)
                except KeyError:
                    pass

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'createScales')
    def createScales(self, instance):
        """creates the scales and save them
        """
        sizes = self.getAvailableSizes(instance)
        if not HAS_PIL or not sizes:
            return
        img = self.getRaw(instance)
        if not img:
            return
        data = str(img.data)
        for n, size in sizes.items():
            w, h = size
            id = self.getName() + "_" + n
            try:
                imgdata, format = self.scale(data, w, h)
            except ConflictError:
                raise
            except:
                if not self.swallowResizeExceptions:
                    raise
                else:
                    log_exc()
                    # scaling failed, don't create a scaled version
                    continue
            image = self.content_class(id, self.getName(),
                                     imgdata,
                                     'image/%s' % format
                                     )
            # manually use storage
            delattr(image, 'title')
            self.getStorage(instance).set(id, instance, image)

    security.declarePrivate('scale')
    def scale(self, data, w, h):
        """ scale image (with material from ImageTag_Hotfix)"""
        #make sure we have valid int's
        size = int(w), int(h)

        pilfilter = PIL.Image.NEAREST
        #check for the pil version and enable antialias if > 1.1.3
        if PIL.Image.VERSION >= "1.1.3":
            pilfilter = PIL.Image.ANTIALIAS

        original_file=StringIO(data)
        image = PIL.Image.open(original_file)
        # consider image mode when scaling
        # source images can be mode '1','L,','P','RGB(A)'
        # convert to greyscale or RGBA before scaling
        # preserve palletted mode (but not pallette)
        # for palletted-only image formats, e.g. GIF
        # PNG compression is OK for RGBA thumbnails
        original_mode = image.mode
        if original_mode == '1':
            image = image.convert('L')
        elif original_mode == 'P':
            image = image.convert('RGBA')
        image.thumbnail(size, pilfilter)
        # XXX: tweak to make the unit test
        #      test_fields.ProcessingTest.test_processing_fieldset run
        format = image.format and image.format or 'PNG'
        # decided to only preserve palletted mode
        # for GIF, could also use   image.format in ('GIF','PNG')
        if original_mode == 'P' and format == 'GIF':
            image = image.convert('P')
        thumbnail_file = StringIO()
        # quality parameter doesn't affect lossless formats
        image.save(thumbnail_file, format, quality=88)
        thumbnail_file.seek(0)
        return thumbnail_file, format.lower()

    security.declareProtected(CMFCorePermissions.View, 'getSize')
    def getSize(self, instance, scale=None):
        """get size of scale or original
        """
        img = self.getScale(instance, scale=scale)
        if not img:
            return 0, 0
        return img.width, img.height

    security.declareProtected(CMFCorePermissions.View, 'getScale')
    def getScale(self, instance, scale=None, **kwargs):
        """Get scale by name or original
        """
        if scale is None:
            return self.get(instance, **kwargs)
        else:
            assert(scale in self.getAvailableSizes(instance).keys(),
                   'Unknown scale %s for %s' % (scale, self.getName()))
            id = self.getScaleName(scale=scale)
            try:
                image = self.getStorage(instance).get(id, instance, **kwargs)
            except AttributeError:
                return ''
            image = self._wrapValue(instance, image, **kwargs)
            if shasattr(image, '__of__', acquire=True) and not kwargs.get('unwrapped', False):
                return image.__of__(instance)
            else:
                return image

    security.declareProtected(CMFCorePermissions.View, 'getScaleName')
    def getScaleName(self, scale=None):
        """Get the full name of the attribute for the scale
        """
        if scale:
            return self.getName() + "_" + scale
        else:
            return ''

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        sizes = self.getAvailableSizes(instance)
        original = self.get(instance)
        size = original and original.get_size() or 0

        if sizes:
            for name in sizes.keys():
                id = self.getScaleName(scale=name)
                try:
                    data = self.getStorage(instance).get(id, instance)
                except AttributeError:
                    pass
                else:
                    size+=data and data.get_size() or 0
        return size

    security.declareProtected(CMFCorePermissions.View, 'tag')
    def tag(self, instance, scale=None, height=None, width=None, alt=None,
            css_class=None, title=None, **kwargs):
        """Create a tag including scale
        """
        image = self.getScale(instance, scale=scale)
        if image:
            img_height=image.height
            img_width=image.width
        else:
            img_height=0
            img_width=0

        if height is None:
            height=img_height
        if width is None:
            width=img_width

        url = instance.absolute_url()
        if scale:
            url+='/' + self.getScaleName(scale)

        values = {'src' : url,
                  'alt' : alt and alt or instance.Title(),
                  'title' : title and title or instance.Title(),
                  'height' : height,
                  'width' : width,
                 }

        result = '<img src="%(src)s" alt="%(alt)s" title="%(title)s" '\
                 'width="%(width)s" height="%(height)s"' % values

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key, value in kwargs.items():
            if value:
                result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

registerField(ImageField,
              title='Image',
              description=('Used for storing images. '
                           'Images can then be retrieved in '
                           'different thumbnail sizes'))


# photo field implementation, derived from CMFPhoto by Magnus Heino
class DynVariantWrapper(Base):
    """Provide a transparent wrapper from image to dynvariant call it
    with url ${image_url}/variant/${variant}
    """

    def __of__(self, parent):
        return parent.Variants()

class DynVariant(Implicit, Traversable):
    """Provide access to the variants."""

    def __init__(self):
        pass

    def __getitem__(self, name):
        if self.checkForVariant(name):
            return self.getPhoto(name).__of__(aq_parent(self))
        else:
            return aq_parent(self)

class ScalableImage(BaseImage):
    """A scalable image class."""

    __implements__ = BaseImage.__implements__

    meta_type = 'Scalable Image'

    isBinary = lambda self: True

    security  = ClassSecurityInfo()

    def __init__(self, id, title='', file='', displays={}):
        BaseImage.__init__(self, id, title, file)
        self._photos = OOBTree()
        self.displays = displays

    # make image variants accesable via url
    variant=DynVariantWrapper()

    security.declareProtected(CMFCorePermissions.View, 'Variants')
    def Variants(self):
        # Returns a variants wrapper instance
        return DynVariant().__of__(self)

    security.declareProtected(CMFCorePermissions.View, 'getPhoto')
    def getPhoto(self,size):
        '''returns the Photo of the specified size'''
        return self._photos[size]

    security.declareProtected(CMFCorePermissions.View, 'getDisplays')
    def getDisplays(self):
        result = []
        for name, size in self.displays.items():
            result.append({'name':name, 'label':'%s (%dx%d)' % (
                name, size[0], size[1]),'size':size}
                )

        #sort ascending by size
        result.sort(lambda d1,d2: cmp(
            d1['size'][0]*d1['size'][0],
            d2['size'][1]*d2['size'][1])
            )
        return result

    security.declarePrivate('checkForVariant')
    def checkForVariant(self, size):
        """Create variant if not there."""
        if size in self.displays.keys():
            # Create resized copy, if it doesnt already exist
            if not self._photos.has_key(size):
                self._photos[size] = BaseImage(
                    size, size, self._resize(self.displays.get(size, (0,0)))
                    )
            # a copy with a content type other than image/* exists, this
            # probably means that the last resize process failed. retry
            elif not self._photos[size].getContentType().startswith('image'):
                self._photos[size] = BaseImage(
                    size, size, self._resize(self.displays.get(size, (0,0)))
                    )
            return True
        else:
            return False

    security.declareProtected(CMFCorePermissions.View, 'index_html')
    def index_html(self, REQUEST, RESPONSE, size=None):
        """Return the image data."""
        if self.checkForVariant(size):
            return self.getPhoto(size).index_html(REQUEST, RESPONSE)
        return BaseImage.index_html(self, REQUEST, RESPONSE)

    security.declareProtected(CMFCorePermissions.View, 'tag')
    def tag(self, height=None, width=None, alt=None,
            scale=False, xscale=False, yscale=False, css_class=None,
            title=None, size='original', **args):
        """Return an HTML img tag (See OFS.Image)"""

        # Default values
        w=self.width
        h=self.height

        if height is None or width is None:

            if size in self.displays.keys():
                if not self._photos.has_key(size):
                    # This resized image isn't created yet.
                    # Calculate a size for it
                    x,y = self.displays.get(size)
                    try:
                        if self.width > self.height:
                            w=x
                            h=int(round(1.0/(float(self.width)/w/self.height)))
                        else:
                            h=y
                            w=int(round(1.0/(float(self.height)/x/self.width)))
                    except ValueError:
                        # OFS.Image only knows about png, jpeg and gif.
                        # Other images like bmp will not have height and
                        # width set, and will generate a ValueError here.
                        # Everything will work, but the image-tag will render
                        # with height and width attributes.
                        w=None
                        h=None
                else:
                    # The resized image exist, get it's size
                    photo = self._photos.get(size)
                    w=photo.width
                    h=photo.height

        if height is None: height=h
        if width is None:  width=w

        # Auto-scaling support
        xdelta = xscale or scale
        ydelta = yscale or scale

        if xdelta and width:
            width =  str(int(round(int(width) * xdelta)))
        if ydelta and height:
            height = str(int(round(int(height) * ydelta)))

        result='<img src="%s/variant/%s"' % (self.absolute_url(), escape(size))

        if alt is None:
            alt=getattr(self, 'title', '')
        result = '%s alt="%s"' % (result, escape(alt, 1))

        if title is None:
            title=getattr(self, 'title', '')
        result = '%s title="%s"' % (result, escape(title, 1))

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if not 'border' in [ x.lower() for x in args.keys()]:
            result = '%s border="0"' % result

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        for key in args.keys():
            value = args.get(key)
            result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

    security.declarePrivate('update_data')
    def update_data(self, data, content_type=None, size=None):
        """
            Update/upload image -> remove all copies
        """
        BaseImage.update_data(self, data, content_type, size)
        self._photos = OOBTree()

    def _resize(self, size, quality=100):
        """Resize and resample photo."""
        image = StringIO()

        width, height = size

        try:
            if HAS_PIL:
                img = PIL.Image.open(StringIO(str(self.data)))
                fmt = img.format
                # Resize photo
                img.thumbnail((width, height))
                # Store copy in image buffer
                img.save(image, fmt, quality=quality)
            else:
                if sys.platform == 'win32':
                    from win32pipe import popen2
                    imgin, imgout = popen2(('convert -quality %s '
                                            '-geometry %sx%s - -'
                                            % (quality, width, height), 'b'))
                else:
                    from popen2 import Popen3
                    convert=Popen3(('convert -quality %s '
                                    '-geometry %sx%s - -'
                                    % (quality, width, height)))
                    imgout=convert.fromchild
                    imgin=convert.tochild

                imgin.write(str(self.data))
                imgin.close()
                image.write(imgout.read())
                imgout.close()

                # Wait for process to close if unix.
                # Should check returnvalue for wait
                if sys.platform !='win32':
                    convert.wait()

                image.seek(0)

        except ConflictError:
            raise
        except Exception, e:
            LOG('Archetypes.ScallableField', ERROR,
                'Error while resizing image', e)

        return image

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setManagerId')
    def ZCacheable_setManagerId(self, manager_id, REQUEST=None):
        '''Changes the manager_id for this object.
           overridden because we must propagate the change to all variants'''
        for size in self._photos.keys():
            variant = self.getPhoto(size).__of__(self)
            variant.ZCacheable_setManagerId(manager_id)
        inherited_attr = Photo.inheritedAttribute('ZCacheable_setManagerId')
        return inherited_attr(self, manager_id, REQUEST)

InitializeClass(ScalableImage)


class PhotoField(ObjectField):
    """A photo field class."""

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'image',
        'default' : '',
        'default_content_type' : 'image/gif',
        'allowable_content_types' : ('image/gif','image/jpeg'),
        'displays': {
            'thumbnail': (128,128),
            'xsmall': (200,200),
            'small': (320,320),
            'medium': (480,480),
            'large': (768,768),
            'xlarge': (1024,1024)
            },
        'widget': ImageWidget,
        'storage': AttributeStorage(),
        })

    security  = ClassSecurityInfo()

    default_view = "view"

    security.declarePrivate('set')
    def set(self, instance, value, **kw):
        if type(value) is StringType:
            value = StringIO(value)
        image = ScalableImage(self.getName(), file=value,
                              displays=self.displays)
        ObjectField.set(self, instance, image, **kw)

    security.declarePrivate('validate_required')
    def validate_required(self, instance, value, errors):
        value = getattr(value, 'get_size', lambda: str(value))()
        return ObjectField.validate_required(self, instance, value, errors)

registerField(PhotoField,
              title='Photo',
              description=('Used for storing images. '
                           'Based on CMFPhoto. ')
             )
