from interfaces.layer import *
from Products.generator.renderer import renderer as base
from debug import log, log_exc

class ArchetypesRenderer(base):
    __implements__ = (ILayer,)

    def render(self, field_name, mode, widget, instance, **kwargs):
        try:
            value = base.render(self, field_name, mode, widget,
                                instance, **kwargs)

        except Exception, E:
            log_exc()
            value = "%s: %s" % (str(type(E)), E)

        return value
    
    def setupContext(self, field_name, mode, widget, instance,
                     **kwargs):

        #Were we passed the context to use or create a new one?
        context = kwargs.get('context')
        if not context:
            context = widget.getContext(instance)
            
        context.beginScope()
        context.setLocal('here', instance)
        context.setLocal('fieldName', field_name)
        context.setLocal('accessor', getattr(instance,
                                             instance.type[field_name].accessor))
        context.setLocal('widget', widget)
        context.setLocal('field', instance.type[field_name])
        context.setLocal('request', instance.REQUEST)
        if kwargs:
            for k,v in kwargs.items():
                context.setLocal(k, v)
                
        return context


renderer = ArchetypesRenderer()

