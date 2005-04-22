from types import ListType, TupleType

from OFS.Image import File
from Products.Archetypes.Field import TextField, FileField
from Products.Archetypes.interfaces.marshall import IMarshall
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.debug import log
from Products.Archetypes.utils import shasattr

from Acquisition import aq_base
from OFS.content_types import guess_content_type

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

class Marshaller:
    __implements__ = IMarshall, ILayer

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

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

    def demarshall(self, instance, data, **kwargs):
        raise NotImplemented

    def marshall(self, instance, **kwargs):
        raise NotImplemented

    def initializeField(self, instance, field):
        pass

    def cleanupField(self, instance, field):
        pass

InitializeClass(Marshaller)

class PrimaryFieldMarshaller(Marshaller):

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def demarshall(self, instance, data, **kwargs):
        p = instance.getPrimaryField()
        file = kwargs.get('file')
        # XXX Hardcoding field types is bad. :(
        if isinstance(p, (FileField, TextField)) and file:
            data = file
            del kwargs['file']
        p.set(instance, data, **kwargs)

    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        if not p:
            raise TypeError, 'Primary Field could not be found.'
        data = p and instance[p.getName()] or ''
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.isImplementedBy(data):
            content_type = data.getContentType()
            length = data.get_size()
            data   = data.getRaw()
        elif isinstance(data, File):
            content_type = data.content_type
            length = data.get_size()
            data = data.data
        else:
            log('WARNING: PrimaryFieldMarshaller(%r): '
                'field %r does not return a IBaseUnit '
                'instance.' % (instance, p.getName()))
            if hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = data and guess_content_type(data) or 'text/plain'
            # XXX FIXME
            # DM 2004-12-01: "FileField"s represent a major field class
            #  that does not use "IBaseUnit" yet.
            #  Ensure, the used "File" objects get the correct length.
            if hasattr(p, 'get_size'):
                length = p.get_size(instance)
            else:
                # DM: this almost surely is stupid!
                length = len(data)

            length = len(data)
            # ObjectField without IBaseUnit?
            if shasattr(data, 'data'):
                data = data.data
            else:
                data = str(data)
                # DM 2004-12-01: recompute 'length' as we now know it definitely
                length = len(data)

        return (content_type, length, data)

InitializeClass(PrimaryFieldMarshaller)

class RFC822Marshaller(Marshaller):

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

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
        content_type = headers.get('Content-Type')
        if not kwargs.get('mimetype', None):
            kwargs.update({'mimetype': content_type})
        p = instance.getPrimaryField()
        # We don't want to pass file forward.
        if kwargs.has_key('file'):
            del kwargs['file']
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
        else:
            if p and hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = body and guess_content_type(body) or 'text/plain'

        headers = []
        fields = [f for f in instance.Schema().fields()
                  if f.getName() != pname]
        for field in fields:
            value = instance[field.getName()]
            if type(value) in [ListType, TupleType]:
                value = '\n'.join([str(v) for v in value])
            headers.append((field.getName(), str(value)))

        headers.append(('Content-Type', content_type or 'text/plain'))

        header = formatRFC822Headers(headers)
        data = '%s\n\n%s' % (header, body)
        length = len(data)

        return (content_type, length, data)

InitializeClass(RFC822Marshaller)

__all__ = ('PrimaryFieldMarshaller', 'RFC822Marshaller', )
