from Acquisition import aq_base
from interfaces.marshall import IMarshall
from interfaces.layer import ILayer
from interfaces.base import IBaseUnit
from StringIO import StringIO
from types import StringType, ListType, TupleType
from debug import log
from OFS.content_types import guess_content_type

class Marshaller:
    __implements__ = (IMarshall, ILayer)

    def __init__(self, demarshall_hook=None, marshall_hook=None):
        self.demarshall_hook = demarshall_hook
        self.marshall_hook = marshall_hook

    def initializeInstance(self, instance, item=None, container=None):
        dm_hook = None
        m_hook = None
        if self.demarshall_hook is not None:
            dm_hook = getattr(instance, self.demarshall_hook, None)
        if self.marshall_hook is not None:
            m_hook = getattr(instance, self.marshall_hook, None)
        instance.demarshall_hook = dm_hook
        instance.marshall_hook = m_hook

    def cleanupInstance(self, instance, item=None, container=None):
        if hasattr(aq_base(instance), 'demarshall_hook'):
            delattr(instance, 'demarshall_hook')
        if hasattr(aq_base(instance), 'marshall_hook'):
            delattr(instance, 'marshall_hook')

class PrimaryFieldMarshaller(Marshaller):

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
            content_type = guess_content_type(data) or 'text/plain'
            length = len(data)
            data = str(data)

        return (content_type, length, data)

class RFC822Marshaller(Marshaller):

    def demarshall(self, instance, data, **kwargs):
        from Products.CMFDefault.utils import parseHeadersBody
        headers, body = parseHeadersBody(data)
        for k, v in headers.items():
            if v.strip() == 'None':
                v = None
            field = instance.getField(k)
            if field is not None:
                mutator = field.getMutator(instance)
                if mutator is not None:
                    mutator(v)
        content_type = headers.get('Content-Type', 'text/plain')
        kwargs.update({'mimetype': content_type})
        p = instance.getPrimaryField()
        if p is not None:
            mutator = p.getMutator(instance)
            if mutator is not None:
                mutator(body, **kwargs)

    def marshall(self, instance, **kwargs):
        from Products.CMFDefault.utils import formatRFC822Headers
        p = instance.getPrimaryField()
        body = p and instance[p.getName()] or ''
        pname = p and p.getName() or None
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.isImplementedBy(body):
            content_type = str(body.getContentType())
            body   = body.getRaw()

        headers = {}
        fields = [f for f in instance.Schema().fields()
                  if f.getName() != pname]
        for field in fields:
            value = instance[field.getName()]
            if type(value) in [ListType, TupleType]:
                value = '\n'.join([str(v) for v in value])
            headers[field.getName()] = str(value)

        headers['Content-Type'] = content_type or 'text/plain'

        header = formatRFC822Headers(headers.items())
        data = '%s\n\n%s' % (header, body)
        length = len(data)

        return (content_type, length, data)
