from interfaces.marshall import IMarshall
from interfaces.layer import ILayer

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
        if hasttr(data, 'isUnit'):
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


