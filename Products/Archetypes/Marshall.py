from interfaces.marshall import IMarshall
from interfaces.layer import ILayer
from StringIO import StringIO
from types import StringType, ListType, TupleType

class Marshaller:
    __implements__ = (IMarshall, ILayer)

    def __init__(self, demarshall_hook=None, marshall_hook=None):
        self.demarshall_hook = demarshall_hook
        self.marshall_hook = marshall_hook

    def initializeInstance(self, instance):
        self.instance.demarshall_hook = getattr(instance, self.demarshall_hook)
        self.instance.marshall_hook = getattr(instance, self.marshall_hook)


class DublinCoreMarshaller(Marshaller):
    ## XXX TODO -- based on CMFCore.Document
    def marshall(self, instance, **kwargs):
        pass

    def demarshall(self, instance, data, **kwargs):
        pass


class PrimaryFieldMarshaller(Marshaller):
    def demarshall(self, instance, data, **kwargs):
        p = instance.getPrimaryField()
        p.set(instance, data, **kwargs)


    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        data = p.get(instance)
        content_type = length = None
        # Gather/Guess content type
        if hasattr(data, 'isUnit'):
            content_type = data.getContentType()
            length = data.get_size()
            data   = data.getRaw()

        #XXX no transform tool
        #else:
        #    ## Use instance to get the transform tool
        #    transformer = getToolByName(instance, 'transform_tool')
        #    content_type = str(transformer.classify(data))
        #    length = len(data)


        if length is None:
            return None

        return (content_type, length, data)

class RFC822Marshaller(Marshaller):

    def demarshall(self, instance, data, **kwargs):
        from Products.CMFDefault.utils import parseHeadersBody
        headers, body = parseHeadersBody(data)
        for k, v in headers.items():
            field = instance.getField(k)
            if field is not None:
                field.set(instance, v, **kwargs)
        content_type = headers.get('Content-Type', 'text/plain')
        kwargs.update({'mime_type': content_type})
        p = instance.getPrimaryField()
        p.set(instance, body, **kwargs)

    def marshall(self, instance, **kwargs):
        from Products.CMFDefault.utils import formatRFC822Headers
        p = instance.getPrimaryField()
        body = p.get(instance)
        content_type = length = None
        # Gather/Guess content type
        if hasattr(body, 'isUnit'):
            content_type = body.getContentType()
            body   = body.getRaw()

        headers = {}
        for field in instance.Schema().fields():
            if field.getName() != p.getName():
                value = instance[field.getName()]
                if type(value) in [ListType, TupleType]:
                    value = '\n'.join([str(v) for v in value])
                headers[field.getName()] = str(value)

        headers['Content-Type'] = content_type or 'text/plain'

        header = formatRFC822Headers(headers.items())
        data = '%s\r\n\r\n%s' % (header, body)
        length = len(data)

        return (content_type, length, data)
