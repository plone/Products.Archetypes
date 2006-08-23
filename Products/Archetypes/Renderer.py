import sys
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper

_marker = []

class ArchetypesRenderer:

    security = ClassSecurityInfo()
    # TODO: more security

    def render(self, field_name, mode, widget, instance=None,
               field=None, accessor=None, **kwargs):
        if field is None:
            field = instance.Schema()[field_name]

        if accessor is None:
            accessor = field.getAccessor(instance)

        context = self.setupContext(field_name, mode, widget,
                                    instance, field, accessor, **kwargs)

        result = widget(mode, instance, context)

        del context
        return result    
    
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

        # for editing of multiple AT-based content at once we might want to
        # prefix the field-name.
        if 'fieldprefix' in kwargs:
            field_name = '%s%s' % (kwargs['fieldprefix'], field_name)

        widget = ImplicitAcquisitionWrapper(widget, instance)
        field = ImplicitAcquisitionWrapper(field, instance)
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

from StringIO import StringIO
from Products.PageTemplates.Expressions import getEngine
engine = getEngine()
from TAL.TALInterpreter import TALInterpreter
from Products.CMFCore.Expression import createExprContext
from Products.CMFPlone.utils import IndexIterator

class AJAXRenderer(BaseRenderer):
    security = ClassSecurityInfo()

    def render(self, field_name, mode, widget, instance=None,
               field=None, accessor=None, **kwargs):
        if field is None:
            field = instance.Schema()[field_name]

        if accessor is None:
            accessor = field.getAccessor(instance)

        context = self.setupContext(field_name, mode, widget,
                                    instance, field, accessor,
                                    **kwargs)
        macro = widget(mode, instance, context)
        buffer = StringIO()
        # evaluate global_defines (to load all the vars we depend on)
        #defines = instance.unrestrictedTraverse("global_defines").macros()['defines']
        #TALInterpreter(macro, {} context, buffer)()
        # Now eval the macro
        TALInterpreter(macro, {}, context, buffer)()
        return buffer.getvalue()


    def setupContext(self, field_name, mode, widget, instance, field, \
                     accessor, **kwargs):

        # create a new context object
        folder = instance.aq_parent
        utool  = instance.portal_url
        portal = utool.getPortalObject()

        context = createExprContext(folder, portal, instance)

        # This seems to be about all we need to fake an AT widgets
        # "interface".. umm, ugh...
        widget = ImplicitAcquisitionWrapper(widget, instance)
        field = ImplicitAcquisitionWrapper(field, instance)
        context.setLocal('here', instance)
        context.setLocal('fieldName', field_name)
        context.setLocal('accessor', accessor)
        context.setLocal('widget', widget)
        context.setLocal('field', field)
        context.setLocal('mode', mode)
        context.setLocal("utool", utool)
        context.setLocal("portal", portal)
        context.setLocal("errors", {})
        context.setLocal("tabindex", IndexIterator(pos=30000))
        # This is a hack but shouldn't matter given that its used for
        # context only in the calls i've seen
        context.setLocal("template", instance)

        return context

InitializeClass(AJAXRenderer)
ajax_renderer = AJAXRenderer()
