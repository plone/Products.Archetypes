import sys

from Products.Archetypes.interfaces.layer import ILayer
from Products.generator.renderer import renderer as base
from Products.Archetypes.debug import log, log_exc
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

_marker = []

class ArchetypesRenderer(base):
    __implements__ = ILayer
    
    security = ClassSecurityInfo()
    # XXX FIXME more security

    def setupContext(self, field_name, mode, widget, instance, field, \
                     accessor, **kwargs):

        # look for the context in the stack
        frame = sys._getframe()
        context = _marker
        while context is _marker and frame is not None:
            context = frame.f_locals.get('econtext', _marker)
            frame = frame.f_back
        if context is _marker:
            raise RuntimeError, 'Context not found'

        context.setLocal('here', instance)
        context.setLocal('fieldName', field_name)
        context.setLocal('accessor', accessor)
        context.setLocal('widget', widget)
        context.setLocal('field', field)
        context.setLocal('mode', mode)

        if kwargs:
            for k,v in kwargs.items():
                context.setLocal(k, v)

        del frame
        return context

InitializeClass(ArchetypesRenderer)

renderer = ArchetypesRenderer()
