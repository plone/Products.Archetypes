from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.content_types import guess_content_type

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.marshallers.base import Marshaller

class PrimaryFieldMarshaller(Marshaller):

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def demarshall(self, instance, data, **kwargs):
        p = instance.getPrimaryField()
        p.set(instance, data, **kwargs)

    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        data = p and instance[p.getName()] or ''
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.isImplementedBy(data):
            content_type = data.getContentType()
            length = data.get_size()
            data   = data.getRaw()
        else:
            log("WARNING: PrimaryFieldMarshaller(%r): field %r does not return a IBaseUnit instance." % (instance, p.getName()))
            if hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = data and guess_content_type(data) or 'text/plain'
            length = len(data)
            # ObjectField without IBaseUnit?
            if hasattr(data, 'data'):
                data = data.data
            else:
                data = str(data)

        return (content_type, length, data)

InitializeClass(PrimaryFieldMarshaller)
