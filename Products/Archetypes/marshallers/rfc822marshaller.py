from types import ListType, TupleType
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.content_types import guess_content_type

from Products.Archetypes.lib.logging import log
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.marshallers.base import Marshaller

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
