from interfaces.layer import *
from Products.generator.renderer import renderer as base
from debug import log, log_exc
import sys

_marker = []

class ArchetypesRenderer(base):
    __implements__ = (ILayer,)

    def setupContext(self, field_name, mode, widget, instance,
                     **kwargs):

        # look for the context in the stack
        try:
            raise RuntimeError
        except RuntimeError:
            frame = sys.exc_info()[2].tb_frame
        context = _marker
        while context is _marker and frame is not None:
            context = frame.f_locals.get('econtext', _marker)
            frame = frame.f_back
        if context is _marker:
            raise RuntimeError, 'Context not found'

        field = instance.Schema()[field_name]
        
        context.setLocal('here', instance)
        context.setLocal('fieldName', field_name)
        context.setLocal('accessor', getattr(instance, field.accessor))
        context.setLocal('widget', widget)
        context.setLocal('field', field)
        if kwargs:
            for k,v in kwargs.items():
                context.setLocal(k, v)
                
        return context


renderer = ArchetypesRenderer()

