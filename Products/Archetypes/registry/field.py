import types
import inspect

from AccessControl import ClassSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from Globals import InitializeClass

from Products.Archetypes.lib.utils import className
from Products.Archetypes.config import DEBUG_SECURITY
from Products.Archetypes.interfaces.base import IBaseObject

class FieldDescription:

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, klass, default_widget=None,
                 title='', description=''):
        self.id = className(klass)
        self.klass = klass
        default_widget = default_widget or klass._properties.get('widget', None)
        if default_widget is None:
            raise ValueError, '%r Must have a default_widget' % klass
        if type(default_widget) not in [types.StringType, types.UnicodeType]:
            default_widget = className(default_widget)
        self.default_widget = default_widget
        self.title = title or klass.__name__
        self.description = description or getDoc(klass)

    def allowed_widgets(self):
        from Products.Archetypes.Registry import availableWidgets
        widgets = []
        for k, v in availableWidgets():
            if v.used_for is None or \
               self.id in v.used_for:
                widgets.append(k)
        return widgets

    def properties(self):
        from Products.Archetypes.Registry import getPropertyType
        props = []
        for k, v in self.klass._properties.items():
            prop = {}
            prop['name'] = k
            prop['type'] = getPropertyType(k, self.klass)
            prop['default'] = v
            props.append(prop)

        return props
