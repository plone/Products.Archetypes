from zope import interface, component
from zope.annotation import IAnnotations
from persistent.dict import PersistentDict

from Products.Archetypes import interfaces

@interface.implementer(interfaces.ITransformCache)
@component.adapter(interfaces.IField, interfaces.IBaseObject)
def transform_cache(field, instance):
    """
    Test if we get a PersistentDict by adapting (field, obj).
    
    >>> from Products.Archetypes.examples.SimpleFile import SimpleFile
    >>> obj = SimpleFile('myFile')
    >>> transforms_cache = component.getMultiAdapter((obj.getField('body'), obj), interfaces.ITransformCache)
    >>> transforms_cache
    <persistent.dict.PersistentDict object at ...>
    
    Test if we get the same value that we put in.
    
    >>> transforms_cache['text/plain'] = 'The text/plain representation of the FileField'
    >>> transforms_cache = component.getMultiAdapter((obj.getField('body'), obj), interfaces.ITransformCache)
    >>> transforms_cache['text/plain']
    'The text/plain representation of the FileField'
    """
    ann = IAnnotations(instance)
    transforms_cache = ann.setdefault(
        'Products.Archetypes:transforms-cache', PersistentDict())
    field_cache = transforms_cache.setdefault(field.getName(), PersistentDict())
    return field_cache
