from copy import deepcopy
from types import DictType

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from Acquisition import aq_base
from Acquisition import aq_inner
from Globals import InitializeClass
from ExtensionClass import Base

from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import createExprContext

from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.logging import log_exc
from Products.Archetypes.lib.utils import className
from Products.Archetypes.lib.utils import capitalize
from Products.Archetypes.translate import translate
from Products.Archetypes.interfaces.widget import IWidget


class BaseWidget:
    """Base class for widgets

    A dynamic widget with a reference to a macro that can be used to
    render it

    description -- tooltip
    label       -- textual label
    visible     -- visible[default] | invisible | hidden
    condition   -- TALES expression to control the widget display
    """

    __implements__ = IWidget

    security  = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess("allow")

    _properties = {
        'description' : '',
        'label' : '',
        'visible' : {'edit':'visible', 'view':'visible'},
        'condition': '',
        }

    def __init__(self, **kwargs):
        # Hey, where's _processed used?!?
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
        value = getattr(self, name, '')
        msgid = getattr(self, name+'_msgid', None) or value

        if not value and not msgid:
            return ''

        domain = (getattr(self, 'i18n_domain', None) or
                  getattr(instance, 'i18n_domain', None))

        if domain is None:
            return value

        return translate(domain, msgid, mapping=instance.REQUEST,
                              context=instance, default=value)

    def Label(self, instance, **kwargs):
        """Returns the label, possibly translated"""
        value = getattr(self, 'label_method', None)
        method = value and getattr(aq_inner(instance), value, None)
        if method and callable(method):
            ## Label methods can be called with kwargs and should
            ## return the i18n version of the description
            value = method(**kwargs)
            return value

        return self._translate_attribute(instance, 'label')

    def Description(self, instance, **kwargs):
        """Returns the description, possibly translated"""
        value = self.description
        method = value and getattr(aq_inner(instance), value, None)
        if method and callable(method):
            ## Description methods can be called with kwargs and should
            ## return the i18n version of the description
            value = method(**kwargs)
            return value

        return self._translate_attribute(instance, 'description')

InitializeClass(BaseWidget)

class MacroWidget(BaseWidget):
    """macro is the file containing the macros, the mode/view is the
    name of the macro in that file
    """

    _properties = BaseWidget._properties.copy()
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
        # Now split the macro into optional parts using '|'
        # if the first part doesn't exist, the search continues
        paths = macro.split('|')
        if len(paths) == 1 and macro == self.macro:
            # prepend the default (optional) customization element
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

InitializeClass(MacroWidget)

class TypesWidget(MacroWidget, Base):
    _properties = MacroWidget._properties.copy()
    _properties.update({
        'modes' : ('view', 'edit'),
        'populate' : True,  # should this field be populated in edit and view?
        'postback' : True,  # should this field be repopulated with POSTed
                         # value when an error occurs?
        'show_content_type' : False,
        'helper_js': (),
        'helper_css': (),
        })

    security = ClassSecurityInfo()

    security.declarePublic('getName')
    def getName(self):
        return self.__class__.__name__

    security.declarePublic('getType')
    def getType(self):
        """Return the type of this field as a string"""
        return className(self)

    security.declarePublic('bootstrap')
    def bootstrap(self, instance):
        """Override if your widget needs data from the instance."""
        return

    security.declarePublic('populateProps')
    def populateProps(self, field):
        """This is called when the field is created."""
        name = field.getName()
        if not self.label:
            self.label = capitalize(name)

    security.declarePublic('isVisible')
    def isVisible(self, instance, mode='view'):
        """decide if a field is visible in a given mode -> 'state'

        Return values are visible, hidden, invisible

        The value for the attribute on the field may either be a dict with a
        mapping for edit and view::

            visible = { 'edit' :'hidden', 'view' : 'invisible' }

        Or a single value for all modes::

            True/1:  'visible'
            False/0: 'invisible'
            -1:      'hidden'

        The default state is 'visible'.
        """
        vis_dic = getattr(aq_base(self), 'visible', _marker)
        state = 'visible'
        if vis_dic is _marker:
            return state
        if type(vis_dic) is DictType:
            state = vis_dic.get(mode, state)
        elif not vis_dic:
            state = 'invisible'
        elif vis_dic < 0:
            state = 'hidden'
        #assert(state in ('visible', 'hidden', 'invisible',),
        #      'Invalid view state %s' % state
        #      )
        return state

    # XXX
    security.declarePublic('setCondition')
    def setCondition(self, condition):
        """Set the widget expression condition."""
        self.condition = condition

    security.declarePublic('getCondition')
    def getCondition(self):
        """Return the widget text condition."""
        return self.condition

    security.declarePublic('testCondition')
    def testCondition(self, folder, portal, object):
        """Test the widget condition."""
        try:
            if self.condition:
                __traceback_info__ = (folder, portal, object, self.condition)
                ec = createExprContext(folder, portal, object)
                return Expression(self.condition)(ec)
            else:
                return True
        except AttributeError:
            return True

    # XXX
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """Basic impl for form processing in a widget"""
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        return value, {}

    security.declarePublic('copy')
    def copy(self):
        """
        Return a copy of widget instance, consisting of field name and
        properties dictionary.
        """
        cdict = dict(vars(self))
        properties = deepcopy(cdict)
        return self.__class__(**properties)

InitializeClass(TypesWidget)
