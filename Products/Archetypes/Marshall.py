import re
from types import ListType, TupleType
from cStringIO import StringIO
from rfc822 import Message

from zope.contenttype import guess_content_type
from zope.interface import implementer

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from OFS.Image import File
from Products.Archetypes.Field import TextField, FileField
from Products.Archetypes.interfaces.marshall import IMarshall
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.log import log
from Products.Archetypes.utils import shasattr
from Products.Archetypes.utils import mapply

sample_data = r"""title: a title
content-type: text/plain
keywords: foo
mixedCase: a MiXeD case keyword

This is the body.
"""


class NonLoweringMessage(Message):
    """A RFC 822 Message class that doesn't lower header names

    IMPORTANT: Only a small subset of the available methods aren't lowering the
               header names!
    """

    def isheader(self, line):
        """Determine whether a given line is a legal header.
        """
        i = line.find(':')
        if i > 0:
            return line[:i]
            # return line[:i].lower()
        else:
            return None

    def getheader(self, name, default=None):
        """Get the header value for a name.
        """
        try:
            return self.dict[name]
            # return self.dict[name.lower()]
        except KeyError:
            return default
    get = getheader


def formatRFC822Headers(headers):
    """ Convert the key-value pairs in 'headers' to valid RFC822-style
        headers, including adding leading whitespace to elements which
        contain newlines in order to preserve continuation-line semantics.

        code based on old cmf1.4 impl
    """
    munged = []
    linesplit = re.compile(r'[\n\r]+?')

    for key, value in headers:

        vallines = linesplit.split(value)
        munged.append('%s: %s' % (key, '\r\n  '.join(vallines)))

    return '\r\n'.join(munged)


def parseRFC822(body):
    """Parse a RFC 822 (email) style string

    The code is mostly based on CMFDefault.utils.parseHeadersBody. It doesn't
    capitalize the headers as the CMF function.

    >>> headers, body = parseRFC822(sample_data)
    >>> keys = headers.keys(); keys.sort()
    >>> for key in keys:
    ...     key, headers[key]
    ('content-type', 'text/plain')
    ('keywords', 'foo')
    ('mixedCase', 'a MiXeD case keyword')
    ('title', 'a title')

    >>> print body
    This is the body.
    <BLANKLINE>
    """
    buffer = StringIO(body)
    message = NonLoweringMessage(buffer)
    headers = {}

    for key in message.keys():
        headers[key] = '\n'.join(message.getheaders(key))

    return headers, buffer.read()


@implementer(IMarshall, ILayer)
class Marshaller:

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
        # TODO Hardcoding field types is bad. :(
        if isinstance(p, (FileField, TextField)) and file:
            data = file
            del kwargs['file']
        mutator = p.getMutator(instance)
        mutator(data, **kwargs)

    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        if not p:
            raise TypeError, 'Primary Field could not be found.'
        data = p and instance[p.getName()] or ''
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.providedBy(data):
            content_type = data.getContentType()
            length = data.get_size()
            data = data.getRaw()
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
                content_type = (data and guess_content_type(data)
                                or 'text/plain')

            # DM 2004-12-01: "FileField"s represent a major field class
            #  that does not use "IBaseUnit" yet.
            #  Ensure, the used "File" objects get the correct length.
            if hasattr(p, 'get_size'):
                length = p.get_size(instance)
            else:
                # DM: this almost surely is stupid!
                length = len(data)

            # ObjectField without IBaseUnit?
            if shasattr(data, 'data'):
                data = data.data
            else:
                data = str(data)
                # DM 2004-12-01: recompute 'length' as we now know it
                # definitely
                length = len(data)

        return (content_type, length, data)

InitializeClass(PrimaryFieldMarshaller)


class RFC822Marshaller(Marshaller):

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def demarshall(self, instance, data, **kwargs):
        # We don't want to pass file forward.
        if 'file' in kwargs:
            if not data:
                # TODO Yuck! Shouldn't read the whole file, never.
                # OTOH, if you care about large files, you should be
                # using the PrimaryFieldMarshaller or something
                # similar.
                data = kwargs['file'].read()
            del kwargs['file']
        headers, body = parseRFC822(data)
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
        p = instance.getPrimaryField()
        body = p and instance[p.getName()] or ''
        pname = p and p.getName() or None
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.providedBy(body):
            content_type = str(body.getContentType())
            body = body.getRaw()
        else:
            if p and hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = body and guess_content_type(
                    body) or 'text/plain'

        headers = []
        fields = [f for f in instance.Schema().fields()
                  if f.getName() != pname]
        for field in fields:
            if field.type in ('file', 'image', 'object'):
                continue
            accessor = field.getEditAccessor(instance)
            if not accessor:
                continue
            kw = {'raw': 1, 'field': field.__name__}
            value = mapply(accessor, **kw)
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
