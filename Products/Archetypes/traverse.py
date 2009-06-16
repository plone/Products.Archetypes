from zope.interface import Interface
from zope.component import adapts
from zope.publisher.interfaces import IRequest
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.atapi import ImageField
from ZPublisher.BaseRequest import DefaultPublishTraverse

class Fallback(Exception): pass

class ImageTraverser(DefaultPublishTraverse):
    adapts(IBaseObject, IRequest)

    def fallback(self, request, name):
        return super(ImageTraverser, self).publishTraverse(request, name)


    def publishTraverse(self, request, name):
        schema=self.context.Schema()

        if "_" in name:
            (fieldname, scale)=name.split("_", 1)
        else:
            (fieldname, scale)=(name, None)

        try:
            field=schema.get(fieldname)
            if field is None:
                raise Fallback

            if not isinstance(field, ImageField):
                raise Fallback

            if scale is not None and scale not in field.getAvailableSizes(self.context):
                raise Fallback

            image=field.getScale(self.context, scale=scale)
            if image is not None and not isinstance(image, basestring):
               return image
        except Fallback:
            pass

        return self.fallback(request, name)


