import tempfile
import posixpath

from zope import event
from zExceptions import MethodNotAllowed
from ZPublisher.Iterators import IStreamIterator
from Products.CMFCore.utils import getToolByName

from Products.Archetypes.event import WebDAVObjectInitializedEvent
from Products.Archetypes.event import WebDAVObjectEditedEvent
from Products.Archetypes.utils import shasattr, mapply
from zope.interface import implementer, Interface


@implementer(IStreamIterator)
class PdataStreamIterator(object):

    def __init__(self, data, size, streamsize=1 << 16):
        # Consume the whole data into a TemporaryFile when
        # constructing, otherwise we might end up loading the whole
        # file in memory or worse, loading objects after the
        # connection is closed.
        f = tempfile.TemporaryFile(mode='w+b')

        while data is not None:
            f.write(data.data)
            data = data.next

        assert size == f.tell(), 'Informed length does not match real length'
        f.seek(0)

        self.file = f
        self.size = size
        self.streamsize = streamsize

    def __iter__(self):
        return self

    def next(self):
        data = self.file.read(self.streamsize)
        if not data:
            self.file.close()
            raise StopIteration
        return data

    def __len__(self):
        return self.size

_marker = []


def collection_check(self):
    if not shasattr(self, '__dav_marshall__'):
        # Backwards-compatible, if property not set ignore.
        return
    if not self.__dav_marshall__:
        # If property is set to a false value, do not allow
        # marshalling.
        raise MethodNotAllowed, 'Method not supported.'


def PUT(self, REQUEST=None, RESPONSE=None):
    """ HTTP PUT handler with marshalling support
    """
    if not REQUEST:
        REQUEST = self.REQUEST
    if not RESPONSE:
        RESPONSE = REQUEST.RESPONSE
    if not self.Schema().hasLayer('marshall'):
        RESPONSE.setStatus(501)  # Not implemented
        return RESPONSE

    self.dav__init(REQUEST, RESPONSE)
    collection_check(self)

    self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
    is_new_object = self.checkCreationFlag()

    file = REQUEST.get('BODYFILE', _marker)
    if file is _marker:
        data = REQUEST.get('BODY', _marker)
        if data is _marker:
            raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
    else:
        data = ''
        file.seek(0)

    mimetype = REQUEST.get_header('content-type', None)
    # mimetype, if coming from request can be like:
    # text/plain; charset='utf-8'
    #
    # XXX we should really parse the extra params and pass them on as
    # keyword arguments.
    if mimetype is not None:
        mimetype = str(mimetype).split(';')[0].strip()

    filename = posixpath.basename(REQUEST.get('PATH_INFO', self.getId()))
    # XXX remove after we are using global services
    # use the request to find an object in the traversal hierachy that is
    # able to acquire a mimetypes_registry instance
    # This is a hack to avoid the acquisition problem on FTP/WebDAV object
    # creation
    parents = (self,) + tuple(REQUEST.get('PARENTS', ()))
    context = None
    for parent in parents:
        if getToolByName(parent, 'mimetypes_registry', None) is not None:
            context = parent
            break

    # Marshall the data
    marshaller = self.Schema().getLayerImpl('marshall')

    args = [self, data]
    kwargs = {'file': file,
              'context': context,
              'mimetype': mimetype,
              'filename': filename,
              'REQUEST': REQUEST,
              'RESPONSE': RESPONSE}
    ddata = mapply(marshaller.demarshall, *args, **kwargs)

    if (shasattr(self, 'demarshall_hook') and self.demarshall_hook):
        self.demarshall_hook(ddata)
    self.manage_afterPUT(data, marshall_data=ddata, **kwargs)
    self.reindexObject()
    self.unmarkCreationFlag()

    if is_new_object:
        event.notify(WebDAVObjectInitializedEvent(self))
    else:
        event.notify(WebDAVObjectEditedEvent(self))

    RESPONSE.setStatus(204)
    return RESPONSE


def manage_FTPget(self, REQUEST=None, RESPONSE=None):
    """Get the raw content for this object (also used for the WebDAV source)
    """

    if REQUEST is None:
        REQUEST = self.REQUEST

    if RESPONSE is None:
        RESPONSE = REQUEST.RESPONSE

    if not self.Schema().hasLayer('marshall'):
        RESPONSE.setStatus(501)  # Not implemented
        return RESPONSE

    self.dav__init(REQUEST, RESPONSE)
    collection_check(self)

    marshaller = self.Schema().getLayerImpl('marshall')
    ddata = marshaller.marshall(self, REQUEST=REQUEST, RESPONSE=RESPONSE)
    if (shasattr(self, 'marshall_hook') and self.marshall_hook):
        ddata = self.marshall_hook(ddata)

    content_type, length, data = ddata

    RESPONSE.setHeader('Content-Type', content_type)
    # Only set Content-Length header length is not None. If we want to
    # support 'chunked' Transfer-Encoding we shouldn't set
    # this. However ExternalEditor *expects* it to be set if we return
    # a StreamIterator, so until that gets fixed we must set it.
    if length is not None:
        RESPONSE.setHeader('Content-Length', length)

    if type(data) is type(''):
        return data

    # We assume 'data' is a 'Pdata chain' as used by OFS.File and
    # return a StreamIterator.
    assert length is not None, 'Could not figure out length of Pdata chain'
    if (issubclass(IStreamIterator, Interface) and IStreamIterator.providedBy(data)
            or not issubclass(IStreamIterator, Interface) and IStreamIterator.IsImplementedBy(data)):
        return data
    return PdataStreamIterator(data, length)


def manage_afterPUT(self, data, marshall_data, file, context, mimetype,
                    filename, REQUEST, RESPONSE):
    """After webdav/ftp PUT method
    """
    pass
