from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.Archetypes.debug import log, log_exc
##XXX remove dep, report errors properly
import i18n

class iwidget:
    def __call__(instance, context=None):
        """return a rendered fragment that can be included in a larger
        context when called by a renderer.

        instance - the instance this widget is called for
        context  - should implement dict behavior
        """

    def getContext(self, mode, instance):
        """returns any prepaired context or and empty {}"""

    def Label(self, instance):
        """Returns the label, possibly translated"""

    def Description(self, instance):
        """Returns the description, possibly translated"""

class widget:
    """
    Base class for widgets

    A dynamic widget with a reference to a macro that can be used to
    render it

    description -- tooltip
    label       -- textual label
    visible     -- 1[default] visible 0 hidden -1 skipped
    """

    __implements__ = (iwidget,)

    security  = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'description' : '',
        'label' : '',
        'visible' : {'edit':'visible', 'view':'visible'},
        'attributes' : ''
        }

    def __init__(self, **kwargs):
        self._processed  = 0
        self._process_args(**kwargs)

    def _process_args(self, **kwargs):
        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)

    def __call__(self, mode, instance, context=None):
        """Not implemented"""
        return ''

    def getContext(self, instance):
        return {}

    def _translate_attribute(self, instance, name):
        value = getattr(self, name)
        domain = getattr(self, 'i18n_domain', None) or getattr(instance, 'i18n_domain', None)
        if domain is None:
            return value
        msgid = getattr(self, name+'_msgid', None) or value
        return i18n.translate(domain, msgid, mapping=instance.REQUEST, context=instance, default=value)

    def Label(self, instance):
        """Returns the label, possibly translated"""
        return self._translate_attribute(instance, 'label')

    def Description(self, instance, **kwargs):
        """Returns the description, possibly translated"""
        value = self.description
        method = getattr(instance.aq_explicit, value, None)
        if method and callable(method):
            ##Description methods can be called with kwargs and should
            ##return the i18n version of the description
            value = method(**kwargs)
            return value

        return self._translate_attribute(instance, 'description')


class macrowidget(widget):
    """macro is the file containing the macros, the mode/view is the
    name of the macro in that file
    """

    _properties = widget._properties.copy()
    _properties.update({
        'macro' : None,
        })

    def bootstrap(self, instance):
        # do initialization-like thingies that need the instance
        pass

    def __call__(self, mode, instance, context=None):
        self.bootstrap(instance)
        #If an attribute called macro_<mode> exists resolve that
        #before the generic macro, this lets other projects
        #create more partial widgets
        macro = getattr(self, "macro_%s" % mode, self.macro)
        template = instance.restrictedTraverse(path = macro)
        return template.macros[mode]

InitializeClass(widget)
