
from types import TupleType, ListType, StringType

from Acquisition import aq_base

from Products.Archetypes.utils import DisplayList
from Products.generator.widget import macrowidget
from Products.Archetypes.Field import ObjectField, Field
from Products.Archetypes.Widget import TypesWidget
from Products.Archetypes.Registry import registerField, registerPropertyType
from Products.Archetypes.ArchetypeTool import getType
from Products.Archetypes.utils import capitalize, mapply, xlate2url, generateId

from ContainerWidgets import *


registerPropertyType('use_class', 'sub class')
registerPropertyType('show_fieldset', 'boolean')
registerPropertyType('show_object_legend', 'boolean')
registerPropertyType('show_object_label', 'boolean')
registerPropertyType('show_select_box', 'boolean')
registerPropertyType('show_move_buttons', 'boolean')
registerPropertyType('show_add_button', 'boolean')
registerPropertyType('show_delete_button', 'boolean')
registerPropertyType('show_id_field', 'boolean')
registerPropertyType('show_sub_fields_label', 'boolean')
registerPropertyType('show_sub_fields_required', 'boolean')
registerPropertyType('show_sub_fields_description', 'boolean')
registerPropertyType('show_main_buttons', 'boolean')
registerPropertyType('show_main_buttons', 'boolean')

def getVocabulary(field, instance):
    """\
    """
    vocabulary=getattr(field, 'vocabulary', None)
    if type(vocabulary) is StringType:
        vocabulary=getattr(instance, vocabulary, None)
    if callable(vocabulary): vocabulary=vocabulary()
    return vocabulary


class ContainerFieldBase(ObjectField):
    """For creating Container sub objects"""

    __implements__ = ObjectField.__implements__

    show_fieldset=1
    show_mini_buttons=0
    show_main_buttons=1

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'objects',
        'default' : (),
        'widget' : ContainerWidget,
        'use_class' : None,
        'show_fieldset' : 1,
        'show_object_legend' : 1,
        'show_object_label' : 1,
        'show_select_box' : 1,
        'show_move_buttons' : 1,
        'show_add_button' : 1,
        'show_delete_button' : 1,
        'show_id_field': 1,
        'show_sub_fields_label' : 1,
        'show_sub_fields_required' : 1,
        'show_sub_fields_description': 0,
        'show_mini_buttons': 0,
        'show_main_buttons': 1,
        })

    def getObjectIds(self, instance, **kwargs):
        vocabulary=getVocabulary(self, instance)
        if isinstance(vocabulary, DisplayList):
            return tuple(vocabulary.keys())
        else:
            name = self.getName()
            storage=self.getStorage()
            kwargs['field'] = self
            try:
                return storage.get(name, instance, **kwargs)
            except:
                default=getattr(self, 'default', ())
                return default

    def getObjectIdsAndLabels(self, instance, **kwargs):
        vocabulary=getVocabulary(self, instance)
        if isinstance(vocabulary, DisplayList):
            return tuple(vocabulary.items())
        else:
            return map(lambda x: (x,x) , getObjectIds(instance, **kwargs))

    def getObjects(self, instance, **kwargs):
        name = self.getName()
        storage=self.getStorage()
        kwargs['field'] = self
        vocabulary=getVocabulary(self, instance)
        if isinstance(vocabulary, DisplayList):
            object_ids=vocabulary.items()
        else:
            object_ids=self.getObjectIds(instance, **kwargs)
        try:
            object_values=[]
            if type(object_ids) is TupleType:
                for id in object_ids:
                    label=None
                    if type(id) is TupleType: id, label=id
                    try:
                        object_values.append(storage.get(id, instance, **kwargs))
                    except:
                        id, obj=self.createObject(instance, id, label=label, **kwargs)
                        storage.set(id, instance, obj, **kwargs)
                        object_values.append(storage.get(id, instance, **kwargs))
        except:
            object_values=()
        return tuple(object_values)


    def getObjectItems(self, instance, **kwargs):
        field_name = self.getName()
        storage=self.getStorage()
        kwargs['field'] = self
        vocabulary=getVocabulary(self, instance)
        if isinstance(vocabulary, DisplayList):
            object_ids=vocabulary.items()
        else:
            object_ids=self.getObjectIds(instance, **kwargs)
        try:
            object_values=[]
            if type(object_ids) is TupleType:
                for id in object_ids:
                    label=None
                    if type(id ) is TupleType: id, label=id
                    try:
                        object_values.append((id, storage.get(id, instance, **kwargs)))
                    except:
                        id, obj=self.createObject(instance, id, label=label, **kwargs)
                        storage.set(id, instance, obj, **kwargs)
                        object_values.append((id, storage.get(id, instance, **kwargs)))

        except:
            object_values=()
        return tuple(object_values)


    def createObject(self, instance, oid=None, label=None, **kwargs):
        use_class=getattr(self, 'use_class', None)
        if use_class is None:
            raise "Invalid Class"
        package,type_name=use_class.split('.')
        if not oid: oid=generateId(type_name)
        pre_id=self.getName()
        object_ids=self.getObjectIds(instance, **kwargs)
        while pre_id+'_'+oid in object_ids:
            oid=generateId(type_name)
            pre_id=self.getName()
        real_id=xlate2url(oid)
        type=getType(type_name, package)
        if not type:
            raise "Invalid Type"

        #
        # Write the created objects id (real_id) to the _created_object_ids
        # If _created_object_ids doesn't match getObjectIds this object needs packing.
        # This enables objects to be created/deleted from a remote list (for instance
        # from a list of ids declared in another field)
        # packing can be either manual (per field) or automatic in the objects
        # setstate.
        #
        field_name = self.getName()
        storage=self.getStorage()
        try: created_object_ids=list(storage.get('_created_object_ids_%s'%field_name, instance))
        except: created_object_ids=[]
        if real_id not in created_object_ids: created_object_ids.append(real_id)
        storage.set('_created_object_ids_%s'%field_name, instance, created_object_ids)

        return real_id, type['klass'](oid, pre_id=pre_id, label=label)


    def get(self, instance, **kwargs):
        raise 'Not Implemented'

    def getRaw(self, instance, **kwargs):
        raise 'Not Implemented'

    def set(self, instance, value, **kwargs):
        raise 'Not Implemented'

    def unset(self, instance, **kwargs):
        raise 'Not Implemented'

    def packingNeeded(self, instance, **kwargs):
        """\
        Checks if getObjectsIds matches the created ids since last pack.
        """
        object_ids=self.getObjectIds(instance, **kwargs)
        field_name = self.getName()
        storage=self.getStorage()
        try: created_object_ids=storage.get('_created_object_ids_%s'%field_name, instance, **kwargs)
        except: created_object_ids=()
        for cid in created_object_ids:
            if cid not in object_ids:
                return 1
        return 0

    def pack(self, instance, **kwargs):
        """\
        Removes orphaned objects whos ids are in _created_object_ids but
        not returned by getObjectIds.
        """
        object_ids=self.getObjectIds(instance, **kwargs)
        field_name = self.getName()
        storage=self.getStorage()
        try: created_object_ids=storage.get('_created_object_ids_%s'%field_name, instance, **kwargs)
        except: created_object_ids=()
        for cid in created_object_ids:
            if cid not in object_ids:
                storage.unset(id, instance, **kwargs)



class ContainerListField(ContainerFieldBase):
    """\
    Contains a list of strings that have a corresponding
    Sub Element associated with them.
    """

    __implements__ = ContainerFieldBase.__implements__

    _properties = ContainerFieldBase._properties.copy()
    _properties.update({
        'type' : 'string',
        'multiValued' : 1,
        'show_fieldset' : 1,
        'show_object_legend' : 1,
        'show_object_label' : 1,
        'show_select_box' : 1,
        'show_move_buttons' : 1,
        'show_add_button' : 1,
        'show_delete_button' : 1,
        'show_id_field': 1,
        'show_sub_fields_label' : 1,
        'show_sub_fields_required' : 1,
        'show_sub_fields_description': 0,
        })



    def get(self, instance, **kwargs):
        #try:
        return self.getObjectIds(instance, **kwargs)
        #except:
        #    raise AttributeError(self.getName())

    def getRaw(self, instance, **kwargs):
        return  self.get(instance, **kwargs)

    def set(self, instance, value, **kwargs):
        name = self.getName()
        storage=self.getStorage()
        object_ids=[]
        deleted_object_ids=kwargs.get('deleted_object_ids', ())
        if type(value) in (TupleType, ListType):
            for id, obj in value:
                if id in deleted_object_ids:
                    try:
                        storage.unset(id, instance, **kwargs)
                    except:
                        pass
                else:
                    object_ids.append(id)
                    storage.set(id, instance, obj, **kwargs)
        storage.set(name, instance, tuple(object_ids), **kwargs)


    def unset(self, instance, **kwargs):
        name = self.getName()
        storage=self.getStorage()
        object_ids=self.getObjectIds(instance, **kwargs)
        if type(object_ids) is TupleType:
            for id in object_ids:
                storage.unset(id, instance, **kwargs)
        storage.unset(name, instance, **kwargs)



registerField(ContainerListField,
              title='ContainerListField',
              description=('Used for storeing Container sub objects which can be '
                           'modified through the parent.'))


class NamedObjectContainerField(ContainerFieldBase):
    """\
    Contains a list of sub elements with ids.
    """

    __implements__ = ContainerFieldBase.__implements__

    _properties = ContainerFieldBase._properties.copy()
    _properties.update({
        'type' : 'objects',
        'show_fieldset' : 1,
        'show_object_legend' : 1,
        'show_object_label' : 1,
        'show_select_box' : 1,
        'show_move_buttons' : 1,
        'show_add_button' : 1,
        'show_delete_button' : 1,
        'show_id_field': 1,
        'show_sub_fields_label' : 1,
        'show_sub_fields_required' : 1,
        'show_sub_fields_description': 0,
        })

    def __repr__(self):
        raise "Not implemented"

class AnonymousObjectContainerField(ContainerFieldBase):
    """\
    Contains a list of sub elements without id.
    """

    __implements__ = ContainerFieldBase.__implements__

    _properties = ContainerFieldBase._properties.copy()
    _properties.update({
        'type' : 'objects',
        'show_fieldset' : 1,
        'show_object_legend' : 1,
        'show_object_label' : 1,
        'show_select_box' : 1,
        'show_move_buttons' : 1,
        'show_add_button' : 1,
        'show_delete_button' : 1,
        'show_id_field': 1,
        'show_sub_fields_label' : 1,
        'show_sub_fields_required' : 1,
        'show_sub_fields_description': 0,
        })

    def __repr__(self):
        raise "Not implemented"


class SingleObjectContainerField(ContainerFieldBase):
    """\
    Contains a list of sub elements without id.
    """

    __implements__ = ContainerFieldBase.__implements__

    _properties = ContainerFieldBase._properties.copy()
    _properties.update({
        'type' : 'objects',
        'show_fieldset' : 1,
        'show_object_legend' : 1,
        'show_object_label' : 1,
        'show_select_box' : 1,
        'show_move_buttons' : 1,
        'show_add_button' : 1,
        'show_delete_button' : 1,
        'show_id_field': 1,
        'show_sub_fields_label' : 1,
        'show_sub_fields_required' : 1,
        'show_sub_fields_description': 0,
        })

    def __repr__(self):
        raise "Not implemented"



