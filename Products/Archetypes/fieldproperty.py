"""Field properties based on Archetypes schema
"""

from DateTime import DateTime
from datetime import datetime
from zope.datetime import parseDatetimetz

from zope.site.hooks import getSite

class ATFieldProperty(object):
    """Field properties based on Archetypes schema

    These properties can only be used on Archetypes objects. They delegate
    to schema.getField(fieldname).get() and set().

    You can use it in your type as follows. The name of the field does
    not need to coincide with the field-property name, but this is probably
    sensible. However, AttributeStorage will interfere here, so we explicitly
    use annoation storage.

        >>> import string
        >>> from Products.Archetypes.atapi import *
        >>> class MyContent(BaseObject):
        ...     portal_type = meta_type = 'MyContent'
        ...     schema = Schema((
        ...         StringField('some_field', storage=AnnotationStorage()),
        ...         StringField('_other_field'),
        ...         ))
        ...
        ...     some_field = ATFieldProperty('some_field')
        ...     other_field = ATFieldProperty('_other_field')
        ...     upper_lower = ATFieldProperty('_other_field',
        ...         get_transform=string.upper, set_transform=string.lower)

        >>> registerType(MyContent, 'Archetypes')

    Now, get and set operations on the fieldproperty behave the same way as
    the mutator and accessor.

        >>> foo = MyContent('foo')
        >>> foo.some_field
        ''
        >>> foo.some_field = "Bar"
        >>> foo.some_field
        'Bar'
        >>> foo.getField('some_field').get(foo)
        'Bar'

    The old-style mutator and accessors still work, of course

        >>> foo.getSome_field()
        'Bar'

        >>> foo.setSome_field("Baz")
        >>> foo.some_field
        'Baz'

    Here is an example using the default AttributeStorage. In this case, we
    need different names for the AT field name and the properity, because
    AttributeStorage will use the field name as the attribute name. If
    you don't do this, you may get infinite recursion!

        >>> foo.other_field = "Hello"
        >>> foo.other_field
        'Hello'
        >>> foo.get_other_field()
        'Hello'
        >>> foo.set_other_field("Good bye")
        >>> foo.other_field
        'Good bye'

    Finally, the get_transform and set_transform arguments can be used to
    perform transformations on the retrieved value and the value before it
    is set, respectively. The field upper_lower uses string.upper() on the
    way out and string.lower() on the way in.

        >>> foo.upper_lower = "MiXeD"
        >>> foo.upper_lower
        'MIXED'
        >>> foo.get_other_field()
        'mixed'
        >>> foo.set_other_field('UpPeRaNdLoWeR')
        >>> foo.upper_lower
        'UPPERANDLOWER'

    A less frivolous example of this functionality can be seen in the
    ATDateTimeFieldProperty class below.
    """

    def __init__(self, name, get_transform=None, set_transform=None):
        self._name = name
        self._get_transform = get_transform
        self._set_transform = set_transform

    def __get__(self, inst, klass):
        if inst is None:
            return self
        field = inst.getField(self._name)
        if field is None:
            raise KeyError("Cannot find field with name %s" % self._name)
        value = field.get(inst)
        if self._get_transform is not None:
            value = self._get_transform(value)
        return value

    def __set__(self, inst, value):
        field = inst.getField(self._name)
        if field is None:
            raise KeyError("Cannot find field with name %s" % self._name)
        if self._set_transform is not None:
            value = self._set_transform(value)
        field.set(inst, value)

class ATToolDependentFieldProperty(ATFieldProperty):
    """A version of the field property type which is able to acquire
    tools. This uses a not-very-nice acquisition hack, and is not
    generalisable to all acquisition-dependent operations, but should work
    for tools in the portal root.

        >>> from Products.Archetypes.atapi import *
        >>> class MyContent(BaseContent):
        ...     portal_type = meta_type = 'MyContent'
        ...     schema = Schema((
        ...         ReferenceField('some_field', multiValued=True,
        ...                        relationship='foo', storage=AnnotationStorage()),
        ...         ))
        ...
        ...     some_field = ATToolDependentFieldProperty('some_field')

        >>> registerType(MyContent, 'Archetypes')

        >>> self.portal._setOb('foo', MyContent('foo'))
        >>> foo = getattr(self.portal, 'foo')

        >>> self.portal._setOb('bar', MyContent('bar'))
        >>> bar = getattr(self.portal, 'bar')
        >>> bar._at_uid = 123456

    These lines would fail with AttributeError: reference_catalog if it used
    the standard accessor.

        >>> foo.some_field
        []
        >>> foo.some_field = [bar]
        Traceback (most recent call last):
        ...
        ReferenceException: 123456 not referenceable
        >>> foo.some_field
        []
    """

    def __init__(self, name, get_transform=None, set_transform=None):
        self._name = name
        self._get_transform = get_transform
        self._set_transform = set_transform

    def __get__(self, inst, klass):
        if inst is None:
            return self
        field = inst.getField(self._name)
        if field is None:
            raise KeyError("Cannot find field with name %s" % self._name)
        value = field.get(inst.__of__(getSite()))
        if self._get_transform is not None:
            value = self._get_transform(value)
        return value

    def __set__(self, inst, value):
        field = inst.getField(self._name)
        if field is None:
            raise KeyError("Cannot find field with name %s" % self._name)
        if self._set_transform is not None:
            value = self._set_transform(value)
        field.set(inst.__of__(getSite()), value)

class ATReferenceFieldProperty(ATToolDependentFieldProperty):
    """A more friendly/use-case-specific name for ATReferenceFieldProperty.
    """

class ATDateTimeFieldProperty(ATFieldProperty):
    """A field property for DateTime fields. This takes care of converting
    to and from a Python datetime.

        >>> from Products.Archetypes.atapi import *
        >>> class MyContent(BaseObject):
        ...     portal_type = meta_type = 'MyContent'
        ...     schema = Schema((
        ...         DateTimeField('date_field', storage=AnnotationStorage()),
        ...         ))
        ...
        ...     date_field = ATDateTimeFieldProperty('date_field')

        >>> registerType(MyContent, 'Archetypes')

    We can now get and set date/times.

        >>> from datetime import datetime
        >>> target_date = datetime(2007, 4, 9, 12, 3, 12)

        >>> foo = MyContent('foo')
        >>> foo.date_field = target_date
        >>> foo.date_field
        datetime.datetime(2007, 4, 9, 12, 3, 12, ...)

        >>> foo.getDate_field().ISO8601()
        '2007-04-09T12:03:12'

        >>> foo.setDate_field(DateTime('2007-04-10 13:11:01'))
        >>> foo.date_field
        datetime.datetime(2007, 4, 10, 13, 11, 1, ...)
    """

    def __init__(self, name):
        super(ATDateTimeFieldProperty, self).__init__(name, self._zope2python_dt, self._python2zope_dt)

    def _zope2python_dt(self, zope_dt):
        if zope_dt is None:
            return None
        return parseDatetimetz(zope_dt.ISO8601())

    def _python2zope_dt(self, python_dt):
        if python_dt is None:
            return None
        return DateTime(python_dt.isoformat())
