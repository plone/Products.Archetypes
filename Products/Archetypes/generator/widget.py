from AccessControl import ClassSecurityInfo
from AccessControl.unauthorized import Unauthorized
from Acquisition import aq_inner
from App.class_init import InitializeClass

from zope.i18n import translate
from zope.i18nmessageid import Message
from zope.interface import Interface, implements

class iwidget(Interface):
    def __call__(instance, context=None):
        """Returns a rendered fragment that can be included in a larger
        context when called by a renderer.

        instance - the instance this widget is called for
        context  - should implement dict behavior
        """

    def getContext(mode, instance):
        """Returns a prepared context or an empty {}."""

    def Label(instance):
        """Returns the label, possibly translated."""

    def Description(instance):
        """Returns the description, possibly translated."""

class widget:
    """Base class for widgets.

    A dynamic widget with a reference to a macro that can be used to
    render it.

    description -- tooltip
    label       -- textual label
    visible     -- visible[default] | invisible | hidden
    condition   -- TALES expression to control the widget display
    """

    implements(iwidget)

    security  = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess('allow')

    _properties = {
        'description' : '',
        'label' : '',
        'visible' : {'edit':'visible', 'view':'visible'},
        'condition': '',
    }

    def __init__(self, **kwargs):
        self._process_args(**kwargs)

    def _process_args(self, **kwargs):
        self.__dict__.update(self._properties)
        self.__dict__.update(kwargs)

    def __call__(self, mode, instance, context=None):
        """Not implemented."""
        return ''

    def getContext(self, instance):
        """Returns a prepared context or an empty {}."""
        return {}

    def _translate_attribute(self, instance, name):
        value = getattr(self, name, '')
        msgid = getattr(self, name+'_msgid', None) or value

        if not value and not msgid:
            return ''

        if isinstance(value, Message):
            return value

        domain = (getattr(self, 'i18n_domain', None) or
                  getattr(instance, 'i18n_domain', None))

        if domain is None:
            return value

        return translate(msgid, domain, context=instance.REQUEST, default=value)

    def Label(self, instance, **kwargs):
        """Returns the label, possibly translated."""
        value = getattr(self, 'label_method', None)
        method = value and getattr(aq_inner(instance), value, None)
        if method and callable(method):
            # Label methods can be called with kwargs and should
            # return the i18n version of the description
            value = method(**kwargs)
            return value
        return self._translate_attribute(instance, 'label')

    def Description(self, instance, **kwargs):
        """Returns the description, possibly translated."""
        value = self.description
        method = value and getattr(aq_inner(instance), value, None)
        if method and callable(method):
            # Description methods can be called with kwargs and should
            # return the i18n version of the description
            value = method(**kwargs)
            return value
        target_language = kwargs.get('target_language', None)
        return self._translate_attribute(instance, 'description')


class macrowidget(widget):
    """Macro is the file containing the macros, the mode/view is the
    name of the macro in that file.
    """

    _properties = widget._properties.copy()
    _properties.update({
        'macro' : None,
    })

    def bootstrap(self, instance):
        # Do initialization-like thingies that need the instance
        pass

    def __call__(self, mode, instance, context=None):
        self.bootstrap(instance)
        # If an attribute called macro_<mode> exists resolve that
        # before the generic macro, this lets other projects
        # create more partial widgets
        macro = getattr(self, 'macro_%s' % mode, self.macro)
        # Now split the macro into optional parts using '|'
        # if the first part doesn't exist, the search continues
        paths = macro.split('|')
        if len(paths) == 1 and macro == self.macro:
            # Prepend the default (optional) customization element
            paths.insert(0, 'at_widget_%s' % self.macro.split('/')[-1])
        for path in paths:
            try:
                template = instance.restrictedTraverse(path = path)
                if template:
                    return template.macros[mode]
            except (Unauthorized, AttributeError, KeyError):
                # This means we didn't have access or it doesn't exist
                pass
        raise AttributeError("Macro %s does not exist for %s" %(macro,
                                                                instance))

InitializeClass(widget)
