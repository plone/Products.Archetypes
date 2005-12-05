import urllib

from zExceptions import MethodNotAllowed
from ZODB.POSException import ConflictError
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import shasattr, mapply

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
        RESPONSE.setStatus(501) # Not implemented
        return RESPONSE

    self.dav__init(REQUEST, RESPONSE)
    collection_check(self)

    self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)

    file = REQUEST.get('BODYFILE', _marker)
    if file is _marker:
        data = REQUEST.get('BODY', _marker)
        if data is _marker:
            raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
    else:
        data = ''
        file.seek(0)

    mimetype = REQUEST.get_header('content-type', None)

    try:
        filename = REQUEST._steps[-2] #XXX fixme, use a real name
    except ConflictError:
        raise
    except:
        filename = (getattr(file, 'filename', None) or
                    getattr(file, 'name', None) or
                    self.getId())
    filename = urllib.unquote_plus(filename)

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
    kwargs = {'file':file,
              'context':context,
              'mimetype':mimetype,
              'filename':filename,
              'REQUEST':REQUEST,
              'RESPONSE':RESPONSE}
    ddata = mapply(marshaller.demarshall, *args, **kwargs)

    if (shasattr(self, 'demarshall_hook') and self.demarshall_hook):
        self.demarshall_hook(ddata)
    self.manage_afterPUT(data, marshall_data = ddata, **kwargs)
    self.reindexObject()
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
        RESPONSE.setStatus(501) # Not implemented
        return RESPONSE

    self.dav__init(REQUEST, RESPONSE)
    collection_check(self)

    marshaller = self.Schema().getLayerImpl('marshall')
    ddata = marshaller.marshall(self, REQUEST=REQUEST, RESPONSE=RESPONSE)
    if (shasattr(self, 'marshall_hook') and self.marshall_hook):
        ddata = self.marshall_hook(ddata)

    content_type, length, data = ddata

    RESPONSE.setHeader('Content-Type', content_type)

    if type(data) is type(''):
        # Only set Content-Length header if we are not streaming,
        # otherwise Zope won't do 'chunked' transfer and even worse, a
        # wrong length can be sent confusing completely the client.
        if length is not None:
            RESPONSE.setHeader('Content-Length', length)
        return data

    # We assume 'data' is a 'Pdata chain' as used by OFS.File and do
    # proper streaming.
    while data is not None:
        # Don't ever set a Content-Length header in this case. Let
        # Zope do the streaming and take care of it doing a proper
        # 'chunked' transfer encoding if the client supports it.
        RESPONSE.write(data.data)
        data = data.next

def manage_afterPUT(self, data, marshall_data, file, context, mimetype,
                    filename, REQUEST, RESPONSE):
    """After webdav/ftp PUT method
    """
    pass
