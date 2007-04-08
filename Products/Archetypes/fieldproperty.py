"""Field properties based on Archetypes schema
"""
_marker = object()

class ATFieldProperty(object):
    """Field properties based on Archetypes schema

    These properties can only be used on Archetypes objects. They delegate
    to schema.getField(fieldname).get() and set().
    
    You can use it in your type as follows. The name of the field does
    not need to conincide with the field-property name, but this is probably
    sensible. However, AttributeStorage will interfere here, so we explicitly
    use annoation storage.
    
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
        
    """

    def __init__(self, name):
        self.__name = name
        
    def __get__(self, inst, klass):
        if inst is None:
            return self
        field = inst.getField(self.__name)
        if field is None:
            raise KeyError("Cannot find field with name %s" % self.__name)
        return field.get(inst)

    def __set__(self, inst, value):
        inst.getField(self.__name).set(inst, value)